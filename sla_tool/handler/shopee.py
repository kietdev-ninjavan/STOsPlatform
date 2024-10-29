import copy
import logging

from django.db import DatabaseError
from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from google_wrapper.services import GoogleSheetService, GoogleDriveService
from google_wrapper.utils import get_service_account
from opv2.services import OrderService
from stos.utils import Configs, chunk_list, parse_datetime, check_record_change
from ..models import ShopeeBacklog

logger = logging.getLogger(__name__)
configs = Configs()


def __initialize_google_sheet_service(spreadsheet_id: str):
    """
    Initializes the GoogleSheetService with the provided service account and spreadsheet ID.
    """
    service_account = get_service_account(configs.get('GAS_WORKER01'))

    try:
        gsheet_service = GoogleSheetService(
            service_account=service_account,
            spreadsheet_id=spreadsheet_id,
            logger=logger
        )
        logger.info('Google Sheet Service initialized successfully')
        return gsheet_service
    except Exception as e:
        logger.error(f'Error initializing Google Sheet Service: {e}')
        raise Exception(f'Error initializing Google Sheet Service: {e}')


def __initialize_google_drive_service():
    """
    Initializes the GoogleDriveService with the provided service account.
    """
    service_account = get_service_account(configs.get('GAS_WORKER01'))
    try:
        google_drive_service = GoogleDriveService(
            service_account=service_account,
            logger=logger
        )
        logger.info('Google Drive Service initialized successfully')
        return google_drive_service
    except Exception as e:
        logger.error(f'Error initializing Google Drive Service: {e}')
        raise Exception(f'Error initializing Google Drive Service: {e}')


def __get_backlog_data(gsheet_service, worksheet):
    # Fetch data from Google Sheet
    gsheet_data = gsheet_service.get_all_records(worksheet)

    if not gsheet_data:
        logger.info('No data found in Google Sheet, skipping processing.')
        return

    total_success = 0
    total_updated = 0
    for chunk in chunk_list(gsheet_data, 1000):
        tracking_ids = [row.get('lm_tracking_no') for row in chunk]
        order_sns = [row.get('order_sn') for row in chunk]

        # Get existing records to avoid duplicates
        existing_records = ShopeeBacklog.objects.filter(
            Q(tracking_id__in=tracking_ids)
            & Q(order_sn__in=order_sns))
        existing_by_tracking_id = {record.tracking_id: record for record in existing_records}

        insert_data, update_data = [], []

        for index, row in enumerate(chunk):
            try:
                backlog_type = row.get('backlog_type', None)
                order_sn = row.get('order_sn', None)
                consignment_no = row.get('consignment_no', None)
                return_sn = row.get('return_sn', None)
                return_id = row.get('return_id', None)
                tracking_id = row.get('lm_tracking_no', None)
                aging_from_lost_threshold = row.get('aging_from_lost_threshold', None)
                create_time = parse_datetime(row.get('create_time'))
                pickup_done_time = parse_datetime(row.get('pickup_done_time'))
            except Exception as e:
                logger.error(f'Error processing row {index + 1}: {e}')
                continue

            backlog = ShopeeBacklog(
                backlog_type=backlog_type,
                order_sn=order_sn,
                consignment_no=consignment_no,
                return_sn=return_sn,
                return_id=return_id,
                tracking_id=tracking_id,
                aging_from_lost_threshold=aging_from_lost_threshold,
                create_time=create_time,
                pickup_done_time=pickup_done_time,
            )

            existing_record = existing_by_tracking_id.get(tracking_id)
            if existing_record:
                is_updated, existing_record, _ = check_record_change(
                    existing_record=existing_record,
                    updated_record=backlog,
                    excluded_fields=['order_id', 'status', 'granular_status', 'rts', 'tracking_id', 'order_sn', 'extended_date', 'extend_days']
                )

                if is_updated:
                    update_data.append(existing_record)
            else:
                insert_data.append(backlog)

        try:
            if insert_data:
                created_records = bulk_create_with_history(
                    insert_data,
                    ShopeeBacklog,
                    ignore_conflicts=True,
                    batch_size=1000
                )
                total_success += len(created_records)
                logger.info(f'Inserted {len(created_records)} new Shopee Backlog {worksheet} records.')
            else:
                logger.info('No new records to insert.')

            if update_data:
                updated_count = bulk_update_with_history(
                    update_data,
                    ShopeeBacklog,
                    fields=[
                        'backlog_type', 'consignment_no', "return_sn", "return_id",
                        'aging_from_lost_threshold', 'create_time', 'pickup_done_time',
                        'updated_date'
                    ],
                    batch_size=1000
                )
                total_updated += updated_count
                logger.info(f'Updated {updated_count} Shopee Backlog {worksheet} records.')
            else:
                logger.info('No records to update.')

        except (DatabaseError, Exception) as e:
            logger.error(f'Error during bulk operations: {e}')
            raise e

    logger.info(f'Successfully inserted {total_success} and updated {total_updated} Shopee Backlog {worksheet} records.')


def collect_shopee_backlogs():
    """
    Collects the Shopee backlogs from the Google Sheet and returns the data.
    """

    # Initialize Google Drive Service
    gdrive_service = __initialize_google_drive_service()

    # Get the Shopee Backlog spreadsheet ID
    yesterday = timezone.now() - timezone.timedelta(days=1)
    file_name = f'Backlog External {yesterday.strftime("%Y-%m-%d")}'

    gs_file = gdrive_service.get_or_convert_to_google_sheet(file_name)

    if not gs_file:
        logger.error('Google Sheet not found, skipping processing.')
        return

    gsheet_service = __initialize_google_sheet_service(gs_file.file_id)

    # FW
    __get_backlog_data(gsheet_service, "FW")

    # RV
    __get_backlog_data(gsheet_service, "RV")


def update_shopee_order_info_form_opv2():
    # Initialize Order Service
    order_service = OrderService(logger=logger)
    # Get all tracking IDs from the database
    qs_orders = ShopeeBacklog.objects.filter(
        Q(aging_from_lost_threshold__in=[0])
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
            ShopeeBacklog,
            fields=[
                'status', 'granular_status', 'order_id', 'rts', 'updated_date'
            ],
            batch_size=1000
        )
        logger.info(f'Updated {updated_count} Shopee Backlog records.')
    else:
        logger.info('No records to update.')
