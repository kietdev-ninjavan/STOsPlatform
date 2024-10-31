import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

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
