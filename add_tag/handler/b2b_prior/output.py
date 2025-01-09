import logging

import pandas as pd
from django.utils import timezone

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import configs

logger = logging.getLogger(__name__)


def out_to_sheet(tracking_ids: list):
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_WORKER03')),
        spreadsheet_id=configs.get('PRIOR_B2B_OUTPUT_SPREADSHEET_ID'),
        logger=logger
    )

    df = pd.DataFrame(tracking_ids, columns=['tracking_id'])
    df['updated_date'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

    gsheet_service.add_dataframe(
        dataframe=df,
        worksheet=configs.get('PRIOR_B2B_OUTPUT_WORKSHEET_ID', cast=int),
        append=True
    )
