import logging

import pandas as pd
from django.db.models import Q

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import configs
from ...models import TicketChangeAddress

logger = logging.getLogger(__name__)


def out_to_gsheet_change_address():
    queryset = TicketChangeAddress.objects.filter(Q(out_sheet=False) & Q(action='Manual Check')).select_related('detect').values(
        'tracking_id',
        'order_id',
        'shipper_id',
        'first_attempt_date',
        'times_change',
        'old_address',
        'province',
        'action',
        'action_reason',
        'rts_flag',
        'ticket_id',
        'created_at',
        'comments',
        'notes',
        'exception_reason',
        'detect__address',
        'detect__province',
        'detect__district',
        'detect__ward',
    )

    if not queryset.exists():
        logger.info('No data to export')
        return

    # Convert queryset to a list of dictionaries
    data = list(queryset)

    # Convert list of dictionaries to a DataFrame
    df = pd.DataFrame(data)

    # Rename columns
    df = df.rename(columns={
        'tracking_id': 'tracking_id',
        'order_id': 'order_id',
        'shipper_id': 'shipper_id',
        'first_attempt_date': 'first_failed_attempt_date',
        'times_change': 'update_address_times',
        'old_address': 'old_address',
        'province': 'province',
        'rts_flag': 'rts_flag',
        'action': 'action',
        'action_reason': 'action_reason',
        'ticket_id': 'ticket_id',
        'created_at': 'ticket_create_at',
        'comments': 'comments',
        'notes': 'notes',
        'exception_reason': 'exception_reason',
        'detect__address': 'detect__address',
        'detect__province': 'detect__province',
        'detect__district': 'detect__district',
        'detect__ward': 'detect__ward',
    })

    # Merge 'comments', 'notes', and 'exception_reason' into one 'notes' column
    try:
        df['notes'] = df[['comments', 'notes', 'exception_reason']].apply(
            lambda row: ' | '.join(filter(None, row)), axis=1
        )
    except KeyError:
        logger.error('Missing columns in DataFrame')

    # Drop the old 'comments', 'notes', and 'exception_reason' columns
    df = df.drop(columns=['comments', 'exception_reason'])

    # Add to Google Sheet
    gsheet_svr = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_WORKER01')),
        spreadsheet_id='1CCUgd6JJdEH2uhg6yTB8rKErCHIEXKcKXLVD6V2p70E',
        logger=logger
    )

    df.to_csv('output.csv', index=False)

    gsheet_svr.add_dataframe(
        df,
        configs.get('OUTPUT_CHANGE_ADDRESS_WORKSHEET_ID', cast=int),
        append=True,
    )

    TicketChangeAddress.objects.filter(Q(out_sheet=False) & Q(action__isnull=False)).update(out_sheet=True)
