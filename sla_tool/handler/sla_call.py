import logging

from simple_history.utils import bulk_create_with_history

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import Configs, chunk_list, parse_datetime
from ..models import BreachSLACall, RecordSLACall

logger = logging.getLogger(__name__)
configs = Configs()


def collect_breach_sla_call():
    """
    Collect breach SLA call data from Google Sheet and store it in the database.
    """

    # Initialize Google Sheet Service
    service_account = get_service_account(configs.get('GSA_BI'))
    gsheet_service = GoogleSheetService(
        service_account=service_account,
        spreadsheet_id=configs.get('SLA_CALL_SPREADSHEET_ID')
    )

    # Get all records from the Google Sheet
    records = gsheet_service.get_all_records(configs.get('SLA_CALL_WORKSHEET_ID', cast=int))

    # Check if records exist
    if not records:
        logger.info('No records found in Google Sheet, skipping processing.')
        return

    total_records = len(records)
    success_records = 0
    for chunk in chunk_list(records, 1000):
        tracking_ids = [row.get('tracking_id') for row in chunk]
        updated_ats = [parse_datetime(row.get('updated_at')) for row in chunk if row.get('updated_at')]

        # Get existing records to avoid duplicates
        existing_pairs = set(
            BreachSLACall.objects.filter(
                tracking_id__in=tracking_ids, updated_at__in=updated_ats
            ).values_list('tracking_id', 'updated_at')
        )

        new_records = []
        for index, row in enumerate(chunk):
            tracking_id = row.get('tracking_id')
            updated_at = parse_datetime(row.get('updated_at')) if row.get('updated_at') else None

            # Skip if record already exists
            if (tracking_id, updated_at) in existing_pairs:
                continue

            try:
                new_records.append(BreachSLACall(
                    tracking_id=tracking_id,
                    granular_status=row.get('granular_status'),
                    order_id=row.get('order_id'),
                    rts=row.get('rts'),
                    shipper_group=row.get('shipper_group'),
                    shipper_name=row.get('shipper_name'),
                    num_of_attempts=row.get('no_attempts'),
                    to_name=row.get('to_name'),
                    to_contact=row.get('to_contact'),
                    to_address1=row.get('to_address1'),
                    cod=row.get('cod_value'),
                    item_description=row.get('item_description'),
                    hub_id=row.get('hub_id'),
                    hub_name=row.get('hub_name'),
                    hub_region=row.get('hub_region'),
                    last_fail_attempt=row.get('last_fail_attempt'),
                    gform_url=row.get('gform_url'),
                    updated_at=updated_at,
                    call_type=row.get('call_type'),
                ))
            except Exception as e:
                logger.error(f'Error processing row {index + 1}: {e}')
                continue

        if not new_records:
            logger.info('No new records to insert.')
            continue

        # Bulk create new records
        created_records = bulk_create_with_history(
            new_records,
            BreachSLACall,
            ignore_conflicts=True,
            batch_size=1000
        )
        success_records += len(created_records)
        logger.info(f'Inserted {len(created_records)} new Breach SLA Call records.')

    logger.info(f'Inserted {success_records}/{total_records} new Breach SLA Call records.')


def collect_record_call():
    """
    Collect record call data from Google Sheet and store it in the database.
    """

    # Initialize Google Sheet Service
    service_account = get_service_account(configs.get('GSA_BI'))
    gsheet_service = GoogleSheetService(
        service_account=service_account,
        spreadsheet_id=configs.get('RECORD_CALL_SPREADSHEET_ID')
    )

    # Get all records from the Google Sheet
    records = gsheet_service.get_all_records(configs.get('RECORD_CALL_WORKSHEET_ID', cast=int))

    # Check if records exist
    if not records:
        logger.info('No records found in Google Sheet, skipping processing.')
        return

    total_records = len(records)
    success_records = 0
    for chunk in chunk_list(records, 1000):
        # Get existing records to avoid duplicates
        tracking_ids = [row.get('tracking_id') for row in chunk]
        existing_tracking_ids = RecordSLACall.objects.filter(tracking_id__in=tracking_ids).values_list('tracking_id', flat=True)

        new_records = []
        for row in chunk:
            tracking_id = row.get('tracking_id')
            # Skip if record already exists
            if tracking_id in existing_tracking_ids or not tracking_id:
                continue

            try:
                new_records.append(RecordSLACall(
                    tracking_id=tracking_id,
                    collect_date=parse_datetime(row.get('collect_date'))
                ))
            except Exception as e:
                logger.error(f'Error processing tracking ID {tracking_id}: {e}')
                continue

        if not new_records:
            logger.info('No new records to insert.')
            continue

        success = bulk_create_with_history(
            new_records,
            RecordSLACall,
            ignore_conflicts=True,
            batch_size=1000
        )
        logger.info(f'Inserted {len(success)} new Record SLA Call records.')
        success_records += len(success)

    logger.info(f'Inserted {success_records}/{total_records} new Record SLA Call records.')
