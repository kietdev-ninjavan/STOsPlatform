import logging

from simple_history.utils import bulk_create_with_history

from redash.client import RedashClient
from stos.utils import configs, chunk_list
from ...models import TicketMissing

logger = logging.getLogger(__name__)


def collect_ticket_missing():
    redash_client = RedashClient(
        api_key=configs.get('REDASH_API_KEY'),
        logger=logger
    )

    try:
        tickets = redash_client.fresh_query_result(2532)
    except Exception as e:
        raise e

    total_tickets = len(tickets)
    total_success = 0
    for chunk in chunk_list(tickets, 1000):
        ticket_ids = [ticket['ticket_id'] for ticket in chunk]

        # Get the existing tickets
        existing_tickets = TicketMissing.objects.filter(ticket_id__in=ticket_ids).values_list('ticket_id', flat=True)
        new_tickets = []
        for ticket in chunk:
            if ticket['ticket_id'] in existing_tickets:
                continue

            try:
                ticket = TicketMissing(
                    ticket_id=ticket.get('ticket_id'),
                    tracking_id=ticket.get('tracking_id'),
                    ticket_status=ticket.get('status_id'),
                    ticket_type=ticket.get('type_id'),
                    ticket_sub_type=ticket.get('subtype_id'),
                    hub_id=ticket.get('hub_id'),
                    investigating_hub_id=ticket.get('investigating_hub_id'),
                    order_id=ticket.get('order_id'),
                    created_at=ticket.get('created_at'),
                    shipper_id=ticket.get('shipper_id'),
                    notes=ticket.get('notes'),
                    ws_last_scan=ticket.get('ws_created_at'),
                    ib_last_scan=ticket.get('ibc_created_at'),
                    sm_last_scan=ticket.get('sm_created_at'),
                )
                new_tickets.append(ticket)
            except Exception as e:
                logger.error(f"Error creating ticket {ticket['ticket_id']}: {e}")
                continue

        success = bulk_create_with_history(new_tickets, TicketMissing, batch_size=1000, ignore_conflicts=True)

        total_success += len(success)
        logger.info(f"Successfully inserted {len(success)} tickets missing records.")

    logger.info(f'Successfully inserted {total_success}/{total_tickets} tickets missing records.')
