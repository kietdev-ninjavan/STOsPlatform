import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_create_with_history
from simple_history.utils import bulk_update_with_history

from opv2.services import OrderService
from redash.client import RedashClient
from stos.utils import configs, chunk_list
from ...models import TicketChangeDate

logger = logging.getLogger(__name__)


def collect_ticket_change_date():
    redash_client = RedashClient(
        api_key=configs.get('REDASH_API_KEY'),
        logger=logger
    )

    try:
        tickets = redash_client.fresh_query_result(2006)
    except Exception as e:
        raise e

    total_tickets = len(tickets)
    total_success = 0
    for chunk in chunk_list(tickets, 1000):
        ticket_ids = [ticket['ticket_id'] for ticket in chunk]

        # Get the existing tickets
        existing_tickets = TicketChangeDate.objects.filter(ticket_id__in=ticket_ids).values_list('ticket_id', flat=True)
        new_tickets = []
        for ticket in chunk:
            if ticket['ticket_id'] in existing_tickets:
                continue

            try:
                ticket = TicketChangeDate(
                    ticket_id=ticket.get('ticket_id'),
                    tracking_id=ticket.get('tracking_id'),
                    ticket_status=ticket.get('status_id'),
                    ticket_type=ticket.get('type_id'),
                    ticket_sub_type=ticket.get('subtype_id'),
                    hub_id=ticket.get('hub_id'),
                    investigating_hub_id=ticket.get('investigating_hub_id'),
                    created_at=ticket.get('created_at'),
                    comments=ticket.get('comments'),
                    notes=ticket.get('ticket_notes'),
                    exception_reason=ticket.get('exception_reason'),
                    first_delivery_date=ticket.get('date_of_1st_delivery_fail'),
                )
                new_tickets.append(ticket)
            except Exception as e:
                logger.error(f"Error creating ticket {ticket['ticket_id']}: {e}")
                continue

        success = bulk_create_with_history(new_tickets, TicketChangeDate, batch_size=1000, ignore_conflicts=True)

        total_success += len(success)
        logger.info(f"Successfully inserted {len(success)} tickets change date records.")

    logger.info(f'Successfully inserted {total_success}/{total_tickets} tickets change date records.')


def load_order_info_change_date():
    tickets = TicketChangeDate.objects.filter(
        Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No ticket to load order info")
        return

    order_svc = OrderService(logger=logger)
    tracking_ids = tickets.values_list('tracking_id', flat=True)
    stt_code, result = order_svc.search_all(tracking_ids)

    if stt_code != 200:
        logger.error(f"Error searching orders: {result}")
        raise Exception("Error searching orders")
    update = []
    for ticket in tickets:
        info = result.get(ticket.tracking_id)
        if not info:
            continue
        ticket.order_id = info.id
        ticket.rts_flag = info.is_rts
        ticket.order_status = info.granular_status
        ticket.updated_date = timezone.now()

        update.append(ticket)

    try:
        success = bulk_update_with_history(
            update,
            TicketChangeDate, batch_size=1000,
            fields=['order_id', 'rts_flag', 'order_status', 'updated_date']
        )

        logger.info(f"Updated {success}/{tickets.count()} tickets' order info")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e
