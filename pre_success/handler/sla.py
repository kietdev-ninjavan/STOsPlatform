import logging

from django.db.models import Q
from django.utils import timezone

from opv2.base.order import GranularStatusChoices
from opv2.dto import CancelTicketDTO
from opv2.services import TicketService
from .collect_data import load_order_info
from .order import pull_route
from ..models import Order

logger = logging.getLogger(__name__)


def pull_route_ovfd():
    # ensure new status is updated
    load_order_info()

    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(granular_status=GranularStatusChoices.on_vehicle)
        & Q(route_id__isnull=True)
        & Q(project_call__icontains='Breach SLA')
    )

    if not orders.exists():
        logger.info("No orders need pull route in the database")
        return

    for order in orders:
        if pull_route(order.order_id):
            logger.info(f"Pull route successfully for order {order.tracking_id}")
        else:
            logger.error(f"Failed to pull route for order {order.tracking_id}")
            continue

    # Ensure new status is updated
    load_order_info()


def cancel_ticket_missing():
    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(ticket_id__isnull=False)
        & Q(route_id__isnull=True)
        & Q(project_call__icontains='Breach SLA')
    )

    if not orders.exists():
        logger.info("No orders need to cancel ticket missing")
        return

    # Cancel ticket missing
    cancel_dtos = [CancelTicketDTO(
        custom_fields=[],
        ticket_id=order.ticket_id,
        tracking_id=order.tracking_id,
        investigating_hub_id=order.investigating_hub_id,
    ) for order in orders]

    # Init ticket service
    ticket_service = TicketService(logger=logger)

    # Cancel ticket missing
    stt_code, result = ticket_service.cancel_tickets(cancel_dtos)

    if stt_code != 200:
        logger.error("Failed to cancel ticket missing")
        return
    success = result.get('success', [])
    failed = result.get('failed', [])
    logger.info(f"Successfully cancel missing tickets: success={success}, failed={failed}")
