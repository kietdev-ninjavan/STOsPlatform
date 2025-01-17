import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.order import GranularStatusChoices
from opv2.services import ScanService, OrderService
from pre_success.models import Order, ShipperGroup
from stos.utils import configs
from .collect_data import load_order_info
from .route import get_route_available, create_route, add_order_to_route

logger = logging.getLogger(__name__)


def parcel_sweeper_live(sla_enabled=False):
    if sla_enabled:
        google_sheet_service = GoogleSheetService(
            service_account=get_service_account(configs.get('GSA_BI')),
            spreadsheet_id=configs.get('PSS_VENDOR_SPREADSHEET_ID'),
            logger=logger
        )

        records = google_sheet_service.get_column(configs.get('QA_IC_WORKSHEET_ID', cast=int), 1)

        if not records:
            logger.warning("No data found in the Google Sheet")

        google_sheetservice = GoogleSheetService(
            service_account=get_service_account(configs.get('GSA_SYSTEM')),
            spreadsheet_id='1vX0HS75LLOQaWKGUZVxcExLb2wCYgeWtCFBRozocgYM',
            logger=logger
        )
        overcapacity = google_sheetservice.read_cell('B2', 1030025293)
        overcapacity_list = list(map(int, overcapacity.split(',')))

        # Filter orders that need processing
        orders = Order.objects.filter(
            Q(created_date__date=timezone.now().date()) &
            Q(granular_status__in=[GranularStatusChoices.arrived_sorting, GranularStatusChoices.en_route]) &
            Q(parcel_sweeper=False) &
            Q(rts=False) &
            ~Q(tracking_id__in=records)
        )
    else:
        # Filter orders that need processing
        orders = Order.objects.filter(
            Q(created_date__date=timezone.now().date()) &
            Q(granular_status__in=[GranularStatusChoices.arrived_sorting, GranularStatusChoices.en_route]) &
            Q(parcel_sweeper=False) &
            Q(rts=False) &
            ~Q(project_call__icontains='Breach SLA')
        )

    # Check if there are any orders to process
    if not orders.exists():
        logger.info("No orders need to update parcel sweeper")
        return

    logger.info(f"Found {orders.count()} orders need to update parcel sweeper")

    # Initialize scanner
    scanner = ScanService(logger=logger)
    successful_updates = []

    # Process each order
    for order in orders:
        if sla_enabled and order.dest_hub_id not in overcapacity_list and order.project_call in 'Gsheet Breach SLA':
            logger.info(f"Order {order.tracking_id} is not in overcapacity list")
            continue

        stt_code, result = scanner.parcel_sweeper_live(tracking_id=order.tracking_id, hub_id=order.dest_hub_id)

        if stt_code != 200:
            logger.error(f"Error in parcel sweeper live for {order.tracking_id}: {result}")
            continue

        # Mark for update
        order.parcel_sweeper = True
        successful_updates.append(order)

    # Perform a bulk update for all successfully scanned orders
    if successful_updates:
        try:
            success = bulk_update_with_history(successful_updates, Order, ['parcel_sweeper'], batch_size=1000)
            logger.info(f"Successfully updated {success}/{len(successful_updates)} orders in bulk")
        except Exception as e:
            logger.error(f"Failed to perform bulk update: {e}")


def reschedule_order():
    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(granular_status=GranularStatusChoices.pending_reschedule)
        & Q(rts=False)
    )

    if not orders.exists():
        logger.info("No orders to reschedule")
        return

    logger.info(f"Found {orders.count()} orders to reschedule")

    # Init Order Service
    order_service = OrderService(logger=logger)

    stt_code, result = order_service.reschedule(orders)

    if stt_code != 200:
        logger.error(f"Error rescheduling orders: {result}")
        return

    logger.info(f"Successfully rescheduled {len(result.get('successful_orders'))} orders")
    logger.info(f"Failed to reschedule {len(result.get('failed_orders'))} orders")

    logger.info('Fetching order info')
    load_order_info()


def pull_route(order_id):
    order_service = OrderService(logger=logger)

    stt_code, result = order_service.pull_route(order_id)

    if stt_code != 200:
        if result['code'] == 103080:
            logger.info('Order no route found route to pull')
            return True

    if stt_code != 200:
        logger.error(f"Error pulling route for order {order_id}: {result}")
        return False

    logger.info(f"Successfully pulled route for order {order_id}")
    return True


def __add_orders_to_route(shipper_group: ShipperGroup):
    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(granular_status__in=[GranularStatusChoices.en_route, GranularStatusChoices.arrived_sorting])
        & Q(parcel_sweeper=True)
        & Q(shipper_group=shipper_group)
        & Q(rts=False)
        & Q(route_id__isnull=True)
    )

    if not orders.exists():
        logger.info(f"No orders available to add to route for {shipper_group}")
        return

    # Get route for shipper group
    route = get_route_available(shipper_group)

    if not route:
        logger.error(f"No route available for {shipper_group}")
        return

    # Assign orders to route
    for order in orders:
        if route.orders.count() >= 200:
            logger.info(f"Route is full, creating a new route for {shipper_group}")
            route = create_route(shipper_group)
            if not route:
                logger.error(f"Failed to create a new route for {shipper_group}")
                return

        if pull_route(order.order_id):
            add_order_to_route(order, route)
            order.route = route
            order.save()


def routing_orders():
    __add_orders_to_route(ShipperGroup.shopee)
    __add_orders_to_route(ShipperGroup.tiktok)
    __add_orders_to_route(ShipperGroup.ttid)
