import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.services import TicketService
from ...models import TicketChangeAddress

logger = logging.getLogger(__name__)


def manual_ticket_have_alo_link():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True)
        & (
                Q(exception_reason__icontains='https://alo.njv.vn')
                | Q(notes__icontains='https://alo.njv.vn')
                | Q(comments__icontains='https://alo.njv.vn')
        )
    )

    if not tickets.exists():
        logger.info("No ALO tickets to manually resolve")
        return

    logger.info(f"Found {tickets.count()} ALO tickets to manually resolve")

    update = []
    for ticket in tickets:
        ticket.action = "Manual Check"
        ticket.action_reason = "Have ALO link"
        ticket.updated_date = timezone.now()
        update.append(ticket)

    try:
        success = bulk_update_with_history(update, TicketChangeAddress, batch_size=1000, fields=['action', 'action_reason', 'updated_date'])
        logger.info(f"Updated {success}/{tickets.count()} tickets' statuses")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def skip_ticket_manual_resolve():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to manually resolve")
        return

    logger.info(f"Found {tickets.count()} tickets to manually resolve")

    tracking_ids = tickets.values_list('tracking_id', flat=True)

    ticket_service = TicketService(logger=logger)

    stt_code, search_tickets = ticket_service.get_ticket_by_tracking_ids(tracking_ids)

    if stt_code != 200:
        logger.error(f"Failed to get tickets: {search_tickets}")
        return

    list_tracking_id_searched = [ticket.tracking_id for ticket in search_tickets]

    for ticket in tickets:
        if ticket.tracking_id not in list_tracking_id_searched:
            ticket.action = "Skip"
            ticket.action_reason = "Order team will handle"
            ticket.updated_date = timezone.now()
            ticket.save()
