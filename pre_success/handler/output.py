import logging

from django.utils import timezone

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import configs

logger = logging.getLogger(__name__)


def add_to_gsheet(driver_id: int, tracking_ids: list):
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_WORKER03')),
        spreadsheet_id=configs.get('PSS_OUTPUT_SPREADSHEET_ID'),
        logger=logger
    )

    worksheet_name = timezone.now().strftime('%d.%m')

    # Duplicate template sheet
    worksheet = gsheet_service.duplicate_worksheet('Template', worksheet_name)

    try:
        row, column = gsheet_service.search_cell(f'{driver_id}', worksheet)
    except Exception as e:
        logger.error(f"Error searching for driver ID: {e}")
        return

    gsheet_service.update_column(
        values=tracking_ids,
        worksheet=worksheet,
        column=column,
        color=True,
        random_color=True
    )


def add_to_pod(driver_name, shipper_group, tracking_ids, new_route=False):
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_WORKER03')),
        spreadsheet_id=configs.get('PSS_OUTPUT_SPREADSHEET_ID'),
        logger=logger
    )

    worksheet_id = configs.get('PSS_POD_WORKSHEET_ID', cast=int)

    # Get column
    try:
        row, column = gsheet_service.search_cell(driver_name, worksheet_id)
    except Exception as e:
        logger.error(f"Error searching for driver name: {e}")
        return

    if new_route:
        gsheet_service.clear_column(
            worksheet=worksheet_id,
            column=column,
            start_row=2
        )
        gsheet_service.update_cell(
            cell=(column, 2),
            value=shipper_group if shipper_group != 'TTDI' else 'TikTok Domestic',
            worksheet=worksheet_id
        )
        gsheet_service.update_column(
            values=tracking_ids,
            worksheet=worksheet_id,
            column=column,
            start_row=3
        )
        return

    gsheet_service.update_column(
        values=tracking_ids,
        worksheet=worksheet_id,
        column=column
    )
