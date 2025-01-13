import logging

from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.dto import TicketResolveDTO
from opv2.services import TicketService
from ...models import TicketChangeAddress

logger = logging.getLogger(__name__)


def __resolve_tickets(tickets, new_instruction, action_reason):
    # Prepare DTOs for resolving tickets
    data_resolve = [
        TicketResolveDTO(
            tracking_id=ticket.tracking_id,
            ticket_id=ticket.ticket_id,
            order_outcome='RTS',
            custom_fields=[],
            new_instruction=new_instruction
        ) for ticket in tickets
    ]

    # Initialize the ticket service and attempt to resolve tickets
    ticket_svc = TicketService(logger=logger)
    stt_code, result = ticket_svc.resolve_tickets(data_resolve)

    if stt_code != 200:
        logger.error(f"Failed to resolve tickets with status code {stt_code}")
        return

    success_ticket_ids = result.get('success', [])
    if not success_ticket_ids:
        logger.warning("No tickets were successfully resolved")
        return

    # Prepare tickets for bulk update
    map_ticket_id = {f'{ticket.ticket_id}': ticket for ticket in tickets}
    tickets_to_update = []
    for ticket_id in success_ticket_ids:
        ticket = map_ticket_id.get(f'{ticket_id}')
        if ticket is None:
            continue

        ticket.action = 'Resolved (RTS)'
        ticket.action_reason = action_reason
        ticket.updated_date = timezone.now()
        tickets_to_update.append(ticket)

    # Attempt bulk update with history
    try:
        success = bulk_update_with_history(
            tickets_to_update,
            TicketChangeAddress,
            batch_size=1000,
            fields=['action', 'action_reason', 'updated_date']
        )
        logger.info(f"Updated {success}/{len(tickets_to_update)} tickets' statuses")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def solve_ticket_have_alo_link():
    tickets = TicketChangeAddress.objects.annotate(
        exception_reason_lower=Lower('exception_reason'),
        notes_lower=Lower('notes'),
        comments_lower=Lower('comments'),
    ).filter(
        Q(action__isnull=True)
        & (
                Q(exception_reason_lower__icontains='https://alo.njv.vn')
                | Q(notes_lower__icontains='https://alo.njv.vn')
                | Q(comments_lower__icontains='https://alo.njv.vn')
        )
        & (
                Q(exception_reason_lower__icontains='đồng ý RTS'.lower())
                | Q(notes_lower__icontains='đồng ý RTS'.lower())
                | Q(comments_lower__icontains='đồng ý RTS'.lower())
        )
    )

    if not tickets.exists():
        logger.info("No ALO tickets to need RTS resolve")
        return

    logger.info(f"Found {tickets.count()} ALO tickets to RTS resolve")

    __resolve_tickets(
        tickets,
        new_instruction='RTS',
        action_reason='Have ALO link'
    )
