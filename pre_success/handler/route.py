import logging
from random import choice

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone

from google_wrapper.services import GoogleChatService
from google_wrapper.utils.card_builder import CardBuilder
from google_wrapper.utils.card_builder import widgets as W
from google_wrapper.utils.card_builder.elements import (
    CardHeader,
    Section,
)
from opv2.base.order import GranularStatusChoices
from opv2.services import RouteService, ScanService
from stos.utils import configs
from .collect_data import load_order_info
from .output import add_to_gsheet, add_to_pod
from ..models import ShipperGroup, Route, Driver

logger = logging.getLogger(__name__)


def create_route(shipper_group: ShipperGroup) -> Route | None:
    route_service = RouteService(logger=logger)

    # Attempt to create a route via the external RouteService
    stt_code, route_id = route_service.create_route()

    if stt_code != 201:
        logger.error(f"Failed to create route for shipper group '{shipper_group.name}' with status code {stt_code}")
        return None

    logger.info(f"Successfully created route {route_id} for shipper group '{shipper_group.name}' on OPv2")

    # Attempt to save the route to the database
    try:
        with transaction.atomic():
            route = Route.objects.create(route_id=route_id, shipper_group=shipper_group)
            logger.info(f"Route {route_id} saved to the database for shipper group '{shipper_group.name}'")
        return route
    except IntegrityError as ie:
        logger.error(f"Integrity error saving route {route_id} for shipper group '{shipper_group.name}': {ie}")
    except Exception as e:
        logger.error(f"Unexpected error saving route {route_id} for shipper group '{shipper_group.name}': {e}")

    return None


def get_route_available(shipper_group: ShipperGroup) -> Route:
    # Filter routes for today, matching the given shipper group and not archived
    routes = Route.objects.filter(
        created_date__date=timezone.now().date(),
        shipper_group=shipper_group,
        archived=False,
    )

    # Return the first available route if any
    if routes.exists():
        route = routes.first()
        if route.orders.count() < 190:
            logger.info(f"Found available route {route.route_id} for shipper group '{shipper_group.name}' with {route.orders.count()} orders")
            return route

    # If no suitable route found, create a new one
    logger.info(f"No available route found for shipper group '{shipper_group.name}', creating a new route")
    return create_route(shipper_group)


def add_order_to_route(order, route):
    route_service = RouteService(logger=logger)

    stt_code, result = route_service.add_order_to_route(order_id=order.order_id, route_id=route.route_id)

    if stt_code != 204:
        logger.error(f"Failed to add order {order.tracking_id} to route {route.route_id}: {result}")
        return False

    logger.info(f"Successfully added order {order.tracking_id} to route {route.route_id}")
    return True


def _build_card(header: str, message: str):
    """
    Builds the Google Chat notification card with task failure details.
    """
    card_builder = CardBuilder()

    # Card Header with current timestamp
    card_header = CardHeader()
    card_header.title = "Pre-Success Tool"
    card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
    card_builder.set_header(card_header)

    # Card Section
    section = Section()
    section.header = f'{header}'

    # Widgets with task details
    section.add_widget(W.TextParagraph(f'{message}'))

    card_builder.add_section(section)

    return card_builder.card


def start_route():
    """
    Query all routes created today and start them.

    Logic:
    1. Filter routes created today and not archived with a driver assigned
    2. For each route, check if there are orders to start
    3. If orders are available, start the route and notify the driver
    4. If all orders are added to the route, notify the driver that the route is started
    5. If no orders are available, log the message and continue to the next route


    """
    routes = Route.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(archived=False)
        & Q(driver__isnull=False)
    )

    if not routes.exists():
        logger.info("No routes to start")
        return

    # Ensure order info is latest
    load_order_info()

    # Initialize the Service
    route_service = RouteService(logger=logger)
    scan_service = ScanService(logger=logger)

    for route in routes:
        total_orders = route.orders.count()
        tracking_ids = [order.tracking_id for order in route.orders.filter(~Q(granular_status=GranularStatusChoices.on_vehicle))]
        waypoint_ids = [order.waypoint_id for order in route.orders.filter(~Q(granular_status=GranularStatusChoices.on_vehicle))]
        if not tracking_ids:
            logger.info(f"Route started {total_orders - len(tracking_ids)}/{total_orders} orders. Skipping route {route.route_id}")
            continue

        # Van Inbound
        stt_code, result = scan_service.van_inbound(route_id=route.route_id, tracking_ids=tracking_ids, waypoint_ids=waypoint_ids)
        if stt_code != 200:
            logger.error(f"Failed to van inbound route {route.route_id}: {result}")
            continue

        stt_code, result = route_service.start_route(route_id=route.route_id, driver_id=route.driver_id, tracking_ids=tracking_ids)

        if stt_code != 200:
            logger.error(f"Failed to start route {route.route_id}: {result}")
            continue

        logger.info(f"Successfully started route {route.route_id}")
        # notify drivers
        if len(tracking_ids) < total_orders:
            card = _build_card(
                header=f"<font color=\"#167a06\"> Route {route.route_id} ({route.driver.driver_name}) </font>",
                message=f"Added {len(tracking_ids)} orders to route"
            )
            add_to_gsheet(route.driver_id, tracking_ids)
            add_to_pod(route.driver.driver_name, route.shipper_group, tracking_ids)
        else:
            card = _build_card(
                header=f"<font color=\"#167a06\"> Route {route.route_id} ({route.driver.driver_name}) </font>",
                message=f"Route started with {total_orders} orders"
            )
            add_to_gsheet(route.driver_id, tracking_ids)
            add_to_pod(route.driver.driver_name, route.shipper_group, tracking_ids, True)

        hook_url = configs.get('PDT_WEBHOOK_URL')
        try:
            # Build and send the Google Chat notification
            chat_service = GoogleChatService(logger=logger)
            chat_service.webhook_send(
                webhook_url=hook_url,
                card=card,
            )
            logger.info(f"Sent Google Chat notification for route {route.route_id}")
        except Exception as notification_exc:
            logger.error(f"Failed to send Google Chat notification for route {route.route_id}: {notification_exc}")
            continue

    # Fetch order info after starting routes
    logger.info('Fetching order info after starting routes')
    load_order_info()


def _check_route_success(route_id: int) -> bool:
    route_service = RouteService(logger=logger)

    stt_code, result = route_service.get_manifest(route_id)
    if stt_code != 200:
        logger.error(f"Failed to get manifest for route {route_id}: {result}")
        return False

    data = result['data']
    if not data:
        logger.error(f"No manifest found for route {route_id}")
        return True

    total_in_route = len(data)
    success_count = sum(1 for item in data if item["status"] == "Success")
    failed_count = sum(1 for item in data if item["status"] == "Fail")
    complete_count = success_count + failed_count

    if complete_count == total_in_route:
        logger.info(f'Route {route_id} is complete: {success_count} success, {failed_count} failed')
        return True

    logger.info(f"Fetch route {route_id} has {complete_count}/{total_in_route} success orders")
    return False


def _archive_route(route_id: int):
    route_service = RouteService(logger=logger)

    stt_code, result = route_service.archive_route(route_id)
    if stt_code != 204:
        logger.error(f"Failed to archive route {route_id}: {result}")
        return False

    logger.info(f"Successfully archived route {route_id}")
    return True


def _fetch_order_in_route(route_id):
    try:
        route = Route.objects.get(route_id=route_id)
    except Route.DoesNotExist:
        logger.error(f"Route {route_id} not found")
        return

    # Initialize the Service
    route_service = RouteService(logger=logger)
    stt_code, result = route_service.get_manifest(route.route_id)

    if stt_code != 200:
        logger.error(f"Failed to get manifest for route {route_id}: {result}")
        return

    data = result['data']
    if not data:
        logger.error(f"No manifest found for route {route_id}")
        return

    route_waypoint_ids = [item['id'] for item in data]
    tracking_ids_pulled = []

    for order in route.orders.all():
        if order.waypoint_id not in route_waypoint_ids:
            tracking_ids_pulled.append(order.tracking_id)
            order.route = None
            try:
                with transaction.atomic():
                    order.save()
                    logger.info(f"Order {order.tracking_id} removed from route {route.route_id}")

                tracking_ids_pulled.append(order.tracking_id)
            except IntegrityError as ie:
                logger.error(f"Integrity error removing order {order.tracking_id} from route {route.route_id}: {ie}")
                continue

    if tracking_ids_pulled:
        card = _build_card(
            header=f"<font color=\"#ab9100\"> Route {route.route_id} <font color=\"#167a06\">",
            message=f"Pulled orders {', '.join(tracking_ids_pulled)} out of route"
        )

        hook_url = configs.get('ROOT_NOTIFICATION_WEBHOOK')
        try:
            # Build and send the Google Chat notification
            chat_service = GoogleChatService(logger=logger)
            chat_service.webhook_send(
                webhook_url=hook_url,
                card=card,
            )
            logger.info(f"Sent Google Chat notification for route {route.route_id}")
        except Exception as notification_exc:
            logger.error(f"Failed to send Google Chat notification for route {route.route_id}: {notification_exc}")
            return


def assign_driver():
    # all driver free
    drivers = list(Driver.objects.filter(
        Q(free=True) &
        Q(enabled=True)
    ))

    if not drivers:
        logger.info("No driver available")
        return

    logger.info(f"Found {len(drivers)} drivers available")

    # all route
    routes = Route.objects.filter(
        created_date__date=timezone.now().date(),
        archived=False,
        driver_id__isnull=True
    ).order_by('created_date')[:len(drivers)]

    if not routes:
        logger.info("No route available")
        return

    logger.info(f"Found {len(routes)} routes available")

    route_service = RouteService(logger=logger)
    for route in routes:
        # random driver
        driver = choice(drivers)

        # OPv2 assign driver
        stt_code, result = route_service.assign_driver(route_id=route.route_id, driver_id=driver.driver_id)

        if stt_code != 204:
            logger.error(f"Failed to assign driver {driver.driver_name} to route {route.route_id}: {result}")
            continue

        # update route
        route.driver = driver
        route.save()
        driver.free = False
        driver.save()

        logger.info(f"Successfully assigned driver {driver.driver_name} to route {route.route_id}")

        # remove driver from list
        drivers.remove(driver)


def fetch_route():
    routes = Route.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(archived=False)
        & Q(driver__isnull=False)
    )

    if routes.exists():
        # Initialize the Service
        for route in routes:
            if not _check_route_success(route.route_id):
                _fetch_order_in_route(route.route_id)
            elif _archive_route(route.route_id):
                try:
                    with transaction.atomic():
                        route.archived = True
                        route.save()
                        logger.info(f"Successfully archived route {route.route_id}")

                        # region Notify
                        card = _build_card(
                            header=f"<font color=\"#167a06\"> Driver {route.driver.driver_name} <font color=\"#167a06\">",
                            message=f"Route {route.route_id} is complete"
                        )

                        hook_url = configs.get('PDT_WEBHOOK_URL')

                        # Build and send the Google Chat notification
                        chat_service = GoogleChatService(logger=logger)
                        chat_service.webhook_send(
                            webhook_url=hook_url,
                            card=card,
                        )
                        logger.info(f"Sent Google Chat notification for route {route.route_id}")
                        # endregion

                except IntegrityError as ie:
                    logger.error(f"Integrity error archiving route {route.route_id}: {ie}")

    # Assign driver to route not assigned
    assign_driver()

    # Start route
    start_route()
