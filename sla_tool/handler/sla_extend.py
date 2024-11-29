import logging

from django.utils import timezone
from simple_history.utils import bulk_create_with_history

from google_wrapper.services import GoogleDriveService
from google_wrapper.utils import get_service_account
from stos.utils import configs, chunk_list, parse_datetime
from ..models import ExtendSLATracking

logger = logging.getLogger(__name__)


def collect_extend_sla(file_name: str = None):
    """
    Collects and stores the extend SLA tracking IDs.
    """
    account_service = get_service_account(configs.get('GSA_BI'))

    # Initialize Google Drive Service
    gdrive_service = GoogleDriveService(service_account=account_service, logger=logger)

    # Find file csv
    two_days_ago = timezone.now() - timezone.timedelta(days=2)
    if not file_name:
        file_name = f'{two_days_ago.strftime("%Y-%m-%d")}-master'
    files = gdrive_service.get_file_by_name(file_name)

    if not files:
        logger.warning(f'No file found with name: {file_name}')
        return

    # Read file csv
    file_content = gdrive_service.csv_get_all_records(files[0].file_id)

    tracking_ids = file_content['tracking_id'].tolist()

    # Get existing tracking IDs
    existing_tracking_ids = ExtendSLATracking.objects.filter(tracking_id__in=tracking_ids).values_list('tracking_id', flat=True)

    new_records = []
    for index, row in file_content.iterrows():
        # Skip existing tracking IDs
        tracking_id = row['tracking_id']
        if tracking_id in existing_tracking_ids:
            continue
        try:
            new_records.append(ExtendSLATracking(
                tracking_id=row['tracking_id'],
                extend_days=row['shopee_extension_days'],
                sla_date=parse_datetime(row['shopee_sla_date']),
                breach_sla_date=parse_datetime(row['shopee_breach_sla_date']),
                first_sla_expectation=parse_datetime(row['shopee_1st_sla_expectation']),
                breach_sla_expectation=parse_datetime(row['shopee_breach_sla_expectation']),
            ))
        except Exception as e:
            logger.error(f'Error processing row {index}|{tracking_id}: {e}')
            continue

    # Bulk create new records
    total_records = len(file_content)
    success_records = 0
    for chunk in chunk_list(new_records, 1000):
        created_records = bulk_create_with_history(
            chunk,
            ExtendSLATracking,
            ignore_conflicts=True,
            batch_size=1000
        )
        success_records += len(created_records)
        logger.info(f'Inserted {len(created_records)} new Extend SLA records.')

    logger.info(f'Inserted {success_records}/{total_records} new Extend SLA records.')
