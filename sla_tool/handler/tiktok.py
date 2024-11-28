import copy
import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.services import OrderService
from stos.utils import configs, chunk_list, parse_datetime, check_record_change
from ..models import TiktokBacklog

logger = logging.getLogger(__name__)


def collect_tiktok_backlogs():
    """
    Collects TikTok backlog data from the Google sheet and stored to database.
    """

    service_account = get_service_account(configs.get('GSA_WORKER01'))
    gsheet_service = GoogleSheetService(
        service_account=service_account,
        spreadsheet_id=configs.get('TIKTOK_BACKLOG_SPREADSHEET_ID'),
        logger=logger
    )

    records = gsheet_service.get_all_records(configs.get('TIKTOK_BACKLOG_WORKSHEET_ID', cast=int))

    if not records:
        logger.info("No records found in the Google Sheet.")
        return

    total_records = len(records)
    success_count = 0
    for chunk in chunk_list(records, 1000):
        tracking_ids = [row.get('Tracking ID') for row in chunk]

        # Get existing records to avoid duplicates
        existing_pairs = set(
            TiktokBacklog.objects.filter(
                tracking_id__in=tracking_ids
            ).values_list('tracking_id', flat=True)
        )

        new_records = []
        for index, row in enumerate(chunk):
            if not row.get('Tracking ID'):
                logger.warning(f'Tracking ID not found in row {index + 1}. Skipping row.')
                continue
            # Skip if the record already exists
            if row.get('Tracking ID') in existing_pairs:
                logger.info(f"Record {index + 1} already exists in the database.")
                continue
            try:
                new_records.append(TiktokBacklog(
                    ticket_no=row.get('Ticket No'),
                    tracking_id=row.get('Tracking ID'),
                    date=parse_datetime(row.get('Date')).date(),
                    shipper_date=parse_datetime(row.get('Date')).date(),
                    backlog_type=row.get('Type')
                ))
            except Exception as e:
                logger.error(f"Error in processing record {index + 1}: {e}")
                continue

        if not new_records:
            logger.info("No valid records to process.")
            continue

        # Bulk create new records
        success = bulk_create_with_history(new_records, TiktokBacklog, batch_size=1000)
        success_count += len(success)
        logger.info(f"Successfully processed {len(success)} out of {len(new_records)} records.")

    logger.info(f"Successfully add new {success_count}/{total_records} records.")


def update_tiktok_order_info_form_opv2(date: timezone.datetime):
    # Initialize Order Service
    order_service = OrderService(logger=logger)

    # Get all tracking IDs from the database
    qs_orders = TiktokBacklog.objects.filter(
        Q(extended_date=date)
    )

    if not qs_orders.exists():
        logger.info('No orders found for the provided tracking IDs.')
        return

    tracking_ids = qs_orders.values_list('tracking_id', flat=True)

    # Search for orders based on the tracking IDs
    status_code, orders = order_service.search_all(tracking_ids)

    if status_code == 404:
        logger.warning('No orders found for the provided tracking IDs.')
        return

    order_has_changed = []
    # Update the orders in the database
    for qs_order in qs_orders:

        tracking_id = qs_order.tracking_id
        order = orders.get(tracking_id)
        new_record = copy.deepcopy(qs_order)
        new_record.status = order.status
        new_record.granular_status = order.granular_status
        new_record.order_id = order.id
        new_record.rts = order.is_rts

        is_updated, existing_record, _ = check_record_change(
            existing_record=qs_order,
            updated_record=new_record,
            excluded_fields=['tracking_id', 'order_sn']
        )

        if is_updated:
            order_has_changed.append(qs_order)

    # Bulk update the orders in the database
    if order_has_changed:
        updated_count = bulk_update_with_history(
            order_has_changed,
            TiktokBacklog,
            fields=[
                'status', 'granular_status', 'order_id', 'rts', 'updated_date'
            ],
            batch_size=1000
        )
        logger.info(f'Updated {updated_count} Tiktok Backlog records.')
    else:
        logger.info('No records to update.')
