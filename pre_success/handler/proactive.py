import logging

from django.db.models import Q
from django.utils import timezone

from opv2.dto import CancelTicketDTO
from opv2.services import TicketService
from ..models import Order

logger = logging.getLogger(__name__)


def cancel_ticket_proactive():
    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(ticket_id__isnull=False)
        & Q(route_id__isnull=True)
        & Q(project_call__icontains='Proactive')
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
        logger.error("Failed to cancel ticket")
        return
    success = result.get('success', [])
    failed = result.get('failed', [])
    logger.info(f"Successfully cancel tickets: success={success}, failed={failed}")
