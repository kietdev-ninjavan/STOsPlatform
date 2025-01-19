import logging

from django.db import transaction

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.ticket import TicketTypeChoices
from opv2.services import TicketService
from stos.utils import configs
from ...models import TicketSelfCollection, SelfCollectionChoices
from simple_history.utils import bulk_create_with_history

logger = logging.getLogger(__name__)


def collect_data_tt():
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_WORKER03')),
        spreadsheet_id=configs.get('SC_SPREADSHEET_ID'),
        logger=logger
    )

    data = gsheet_service.get_all_records_as_dataframe(configs.get('SC_WORKSHEET_ID', cast=int), head_row=0)

    data = data[data['aging'] > 14]

    tracking_ids = data['tracking_id'].tolist()

    logger.info(f"Got {len(tracking_ids)} tracking ids")

    if not tracking_ids:
        logger.info("No tracking ids found")
        return

    ticket_svc = TicketService(logger)

    stt_code, tickets = ticket_svc.get_ticket_by_tracking_ids(tracking_ids, ticket_types=[TicketTypeChoices.SELF_COLLECTION])

    if stt_code != 200:
        raise Exception(f"Error when get tickets: {tickets}")

    if len(tickets) == 0:
        logger.info("No tickets found")
        return
    new_tickets = []
    for ticket in tickets:
        try:
            ticket_status = ticket.status.value
            ticket_self_collection = TicketSelfCollection(
                ticket_id=ticket.id,
                tracking_id=ticket.tracking_id,
                ticket_status=ticket_status,
                ticket_type=ticket.type,
                ticket_sub_type=ticket.sub_type,
                hub_id=ticket.hub_id,
                investigating_hub_id=ticket.investigating_hub_id,
                type=SelfCollectionChoices.TT_DESTROYED_GOODS,
            )
            new_tickets.append(ticket_self_collection)
        except Exception as e:
            logger.error(f"Error when create ticket self collection: {e}")
            continue

    if new_tickets:
        try:
            with transaction.atomic():
                TicketSelfCollection.objects.bulk_create(new_tickets, batch_size=1000, ignore_conflicts=True)
            logger.info(f"Successfully created {len(new_tickets)} tickets")
        except Exception as e:
            logger.error(f"Error when create ticket self collection: {e}")
