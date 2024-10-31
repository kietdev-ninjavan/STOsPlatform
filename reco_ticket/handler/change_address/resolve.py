import logging

from django.db.models import F, ExpressionWrapper, fields, Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.base.order import GranularStatusChoices
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

        ticket.action = 'Resolved (Resume Delivery)'
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


def resolved_rts_and_last_status():
    """
    Resolves tickets that are either RTS or have a last status of 'Cancelled' or 'Completed'.
    """

    # Filter tickets that are RTS or have a last status of 'Cancelled' or 'Completed'
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        (
                Q(rts_flag=True) |
                Q(order_status__in=[GranularStatusChoices.completed, GranularStatusChoices.cancelled])
        )
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    logger.info(f"Found {tickets.count()} tickets to resolve")

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. Order is RTS or has a granular status of Cancelled/Completed.',
        action_reason='Order is RTS or has a granular status of Cancelled/Completed'
    )


def resolved_ticket_system_create():
    four_hours_ago = timezone.now() - timezone.timedelta(hours=4)

    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        Q(created_at__lte=four_hours_ago) &
        Q(exception_reason__isnull=True) &
        Q(comments__isnull=True) &
        Q(notes__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    logger.info(f"Found {tickets.count()} tickets to resolve")

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. Ticket created > 4h and no filled reason.',
        action_reason='Ticket created > 4h and no filled reason'
    )


def resolved_ticket_storage_max_stored():
    """
    Resolves tickets that were created more than 5 days after the first attempt date.
    """
    tickets = TicketChangeAddress.objects.filter(
        Q(first_attempt_date__isnull=False)  # Ensure first_failed_attempt_date is not null
        & Q(created_at__gt=ExpressionWrapper(
            F('first_attempt_date') + timezone.timedelta(days=5),
            output_field=fields.DateTimeField()
        ))
        & Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    logger.info(f"Found {tickets.count()} tickets to resolve")

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. The order has been stored for more than 5 days.',
        action_reason='Ticket created > 5 days after first failed attempt'
    )


def resolved_have_changed_address():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        Q(times_change__gt=0)
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. Order has updated address more than once.',
        action_reason='Order has updated address more than once'
    )


def resolved_ticket_tokgistics():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        Q(first_attempt_date__isnull=True) &
        Q(shipper_id=7314925)
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. No first delivery attempt.',
        action_reason='Order has shipper TOKGISTIC PTE. LTD (7314925) and no first delivery attempt'
    )


def resolved_ticket_incorrect_format():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        (Q(detect__province__isnull=True)
         | Q(detect__district__isnull=True)
         | Q(detect__ward__isnull=True)
         )
    )

    if not tickets.exists():
        logger.info("No tickets to resolve")
        return

    __resolve_tickets(
        tickets,
        new_instruction='Auto resolved by system. Incorrect format. Please create new ticket correct format.',
        action_reason='Incorrect format'
    )
