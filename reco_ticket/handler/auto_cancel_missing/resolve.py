import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.dto.ticket_dto import TicketResolveDTO
from opv2.services import TicketService
from ...models import TicketMissing

logger = logging.getLogger(__name__)


def check_need_resolve():
    tickets = TicketMissing.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(need_resolve=False)
    )

    if not tickets.exists():
        logger.info("No ticket to check resolve")
        return

    logger.info(f"Found {tickets.count()} tickets need to check resolve")

    update = []
    for ticket in tickets:
        scan_dates = [date for date in [ticket.ws_last_scan, ticket.sm_last_scan, ticket.ib_last_scan] if date]
        last_scan = max(scan_dates) if scan_dates else None
        if last_scan == ticket.ws_last_scan or last_scan == ticket.ib_last_scan:
            ticket.need_resolve = True
            update.append(ticket)
        elif last_scan == ticket.sm_last_scan:
            continue

    if update:
        try:
            success = bulk_update_with_history(update, TicketMissing, ['need_resolve'], batch_size=1000)
            logger.info(f"Successfully updated {success}/{len(update)} tickets in bulk")
        except Exception as e:
            logger.error(f"Failed to perform bulk update: {e}")


def resolve_missing():
    tickets = TicketMissing.objects.filter(
        Q(created_date__date=timezone.now().date())
        & Q(need_resolve=True)
        & Q(resolve_at__isnull=True)
    )

    if not tickets.exists():
        logger.info("No ticket to resolve")
        return

    logger.info(f"Found {tickets.count()} tickets need to resolve")

    # Init Ticket Service
    ticket_service = TicketService(logger=logger)

    data_resolve = [
        TicketResolveDTO(
            tracking_id=ticket.tracking_id,
            ticket_id=ticket.ticket_id,
            order_outcome='FOUND - INBOUND',
            custom_fields=[],
            new_instruction=''
        ) for ticket in tickets
    ]

    stt_code, result = ticket_service.resolve_tickets(data_resolve)

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

        ticket.resolve_at = timezone.now()
        ticket.updated_date = timezone.now()
        tickets_to_update.append(ticket)

    # Attempt bulk update with history
    try:
        success = bulk_update_with_history(
            tickets_to_update,
            TicketMissing,
            batch_size=1000,
            fields=['resolve_at', 'updated_date']
        )
        logger.info(f"Updated {success}/{len(tickets_to_update)} tickets'")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e
