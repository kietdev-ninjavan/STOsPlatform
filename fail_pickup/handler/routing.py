import logging
import time

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.base.pickup import PickupJobStatusChoices
from opv2.services import RouteService, PickupService
from .collect_data import collect_job_info
from ..models import PickupJob, Route, PickupJobOrder

logger = logging.getLogger(__name__)


def __create_route():
    route_service = RouteService(logger=logger)

    # Create a new route
    stt_code, route_id = route_service.create_route(driver_id=1682343)

    if stt_code != 201:
        logger.error('Failed to create route for driver')
        raise Exception(f'Failed to create route as {route_id}')

    try:
        with transaction.atomic():
            Route.objects.create(
                route_id=route_id,
                driver_id=1682343
            )
    except Exception as e:
        logger.error(f'Failed to create route in database: {e}')
        raise Exception('Failed to create route in database')

    return route_id


def __route_available() -> Route:
    try:
        route = Route.objects.get(
            Q(created_date__date=timezone.now().date()) &
            Q(archived=False)
        )
        return route
    except Route.DoesNotExist:
        route_id = __create_route()
        try:
            route = Route.objects.get(route_id=route_id)
        except Route.DoesNotExist:
            logger.error(f'Route with id {route_id} does not exist')
            raise Exception(f'Route with id {route_id} does not exist')
        return route


def job_routing():
    pickup_jobs = PickupJob.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(route_id__isnull=True) &
        Q(status=PickupJobStatusChoices.READY_FOR_ROUTING)
    )

    if not pickup_jobs.exists():
        logger.info('No job for routing, skipping processing.')
        return

    logger.info(f'Found {pickup_jobs.count()} for routing')

    route = __route_available()

    # Init pickup service
    pickup_service = PickupService(logger=logger)

    update = []
    for pickup_job in pickup_jobs:
        stt_code, result = pickup_service.add_route(
            pickup_job_id=pickup_job.job_id,
            route_id=route.route_id
        )

        if stt_code != 200:
            logger.error(f'Failed to add route for pickup job {pickup_job.job_id}: {result}')
            continue

        pickup_job.route = route
        pickup_job.updated_date = timezone.now()

        update.append(pickup_job)

    try:
        success = bulk_update_with_history(update, PickupJob, ['route', 'updated_date'], batch_size=1000)
        logger.info(f'Successfully updated {success} records')
    except Exception as e:
        logger.error(f'Failed to update records: {e}')
        raise Exception('Failed to update records')

    # Collect job info
    logger.info('Collecting job info after routing delay 10s')
    time.sleep(10)
    collect_job_info()
    logger.info('Collected job info after routing')


def start_route():
    collect_job_info()
    route = Route.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(archived=False)
    ).first()

    if not route:
        logger.info('No route to start')
        return

    tracking_ids = PickupJobOrder.objects.filter(
        Q(job_id__driver_id=1682343) &
        Q(job_id__route_id=route.route_id) &
        Q(job_id__status=PickupJobStatusChoices.ROUTED)
    ).values_list('tracking_id', flat=True)

    route_service = RouteService(logger=logger)

    stt_code, result = route_service.start_route(
        route_id=route.route_id,
        driver_id=1682343,
        tracking_ids=tracking_ids
    )

    if stt_code != 200:
        logger.error(f'Failed to start route: {result}')
        raise Exception(f'Failed to start route: {result}')

    logger.info(f'Started route {route.route_id}')

    # Update status
    logger.info('Updating status after starting route')
    time.sleep(10)
    collect_job_info()
    logger.info('Updated status after starting route')


def archive_route():
    routes = Route.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(archived=False)
    )

    if not routes.exists():
        logger.info('No route to archive')
        return

    route_service = RouteService(logger=logger)

    for route in routes:
        stt_code, result = route_service.archive_route(route_id=route.route_id)

        if stt_code != 204:
            logger.error(f'Failed to archive route: {result}')
            raise Exception(f'Failed to archive route: {result}')

    try:
        with transaction.atomic():
            routes.update(archived=True)
    except Exception as e:
        logger.error(f'Failed to archive route in database: {e}')
        raise Exception('Failed to archive route in database')
