import logging

from django.db.models import Q, F
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.base.order import GranularStatusChoices
from opv2.dto import TicketResolveDTO
from opv2.services import TicketService
from ...models import TicketChangeDate

logger = logging.getLogger(__name__)


def __resolve_tickets(tickets, new_instruction, action, action_reason):
    # Prepare DTOs for resolving tickets
    data_resolve = [
        TicketResolveDTO(
            tracking_id=ticket.tracking_id,
            ticket_id=ticket.ticket_id,
            order_outcome='RESUME DELIVERY',
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

        ticket.action = action
        ticket.action_reason = action_reason
        ticket.apply_action = timezone.now()
        ticket.updated_date = timezone.now()
        tickets_to_update.append(ticket)

    # Attempt bulk update with history
    try:
        success = bulk_update_with_history(
            tickets_to_update,
            TicketChangeDate,
            batch_size=1000,
            fields=['action', 'updated_date', 'action_reason', 'apply_action']
        )
        logger.info(f"Updated {success}/{len(tickets_to_update)} tickets' statuses")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def not_have_first_delivery_date():
    tickets = TicketChangeDate.objects.filter(
        Q(first_delivery_date__isnull=True)
        & Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to not have first delivery date")
        return

    __resolve_tickets(
        tickets,
        'Auto resolved by system. Not have first attempt.',
        'Reject',
        'Not have first attempt'
    )


def have_rts_or_last_status():
    tickets = TicketChangeDate.objects.filter(
        (Q(rts_flag=True) |
         Q(order_status__in=[GranularStatusChoices.completed, GranularStatusChoices.cancelled])) &
        Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to RTS or last status")
        return

    __resolve_tickets(
        tickets,
        'Auto resolved by system. Order is RTS or has a granular status of Cancelled/Completed.',
        'Reject',
        'Order is last status or RTS'
    )


def more_than_five_date():
    tickets = TicketChangeDate.objects.filter(
        Q(detected_date__gt=F('first_delivery_date') + timezone.timedelta(days=5))
        & Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to more than five date")
        return

    __resolve_tickets(
        tickets,
        'Auto resolved by system. Greater than 5 days',
        'Reject',
        'Greater than 5 days'
    )


def incorrect_format_date():
    tickets = TicketChangeDate.objects.filter(
        Q(detected_date__isnull=True)
        & Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to incorrect format")
        return

    __resolve_tickets(
        tickets,
        'Auto resolved by system. Incorrect format. Please create new ticket correct format.',
        'Reject',
        'Incorrect format'
    )


def approve_tickets():
    tickets = TicketChangeDate.objects.filter(
        Q(action__isnull=True) &
        Q(detected_date__isnull=False)
    )

    if not tickets.exists():
        logger.info("No tickets to approve")
        return

    tickets_to_update = []
    for ticket in tickets:
        ticket.action = 'Approve'
        ticket.action_reason = 'Normal Approve'
        ticket.updated_date = timezone.now()
        tickets_to_update.append(ticket)

    # Attempt bulk update with history
    try:
        success = bulk_update_with_history(
            tickets_to_update,
            TicketChangeDate,
            batch_size=1000,
            fields=['action', 'updated_date']
        )
        logger.info(f"Updated {success}/{len(tickets_to_update)} tickets' statuses")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def apply_action():
    tickets = TicketChangeDate.objects.filter(
        Q(action='Approve') &
        Q(apply_action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to apply action")
        return

    __resolve_tickets(
        tickets,
        'Auto resolved by system. Approved by system.',
        'Approve',
        'Normal Approve',
    )
