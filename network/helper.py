from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
import logging
from stos.utils import configs
from .models import HubB2B, Hub
logger = logging.getLogger(__name__)


def manual_sync_b2b_zone():
    service_account = get_service_account(configs.get('GSA_SYSTEM'))
    gsheets_service = GoogleSheetService(
        service_account=service_account,
        spreadsheet_id='1UOwAr23IayOVQcHETwNL1o1dTT9ZD6oetL3wgXV8cKg',
        logger=logger
    )

    # Get the data from the Google Sheet
    data = gsheets_service.get_all_records(0)

    # Process the data
    update = []
    for row in data:
        hub_id = row.get('id')
        b2b_hub = row.get('b2b_hub')

        # Get the Hub object
        hub = Hub.objects.get(id=hub_id)

        if not hub:
            logger.warning(f"Hub with ID {hub_id} not found.")
            continue

        # Get the B2B Hub object
        b2b_hub_obj = HubB2B.objects.get(hub_name=b2b_hub)

        if not b2b_hub_obj:
            logger.warning(f"B2B Hub with name {b2b_hub} not found.")
            continue

        # Update the Hub object
        hub.b2b_hub = b2b_hub_obj
        update.append(hub)


    # Bulk update the Hub objects
    Hub.objects.bulk_update(update, ['b2b_hub'])

    logger.info(f"B2B Hub sync completed. {len(update)}/{len(data)} Hubs updated.")
