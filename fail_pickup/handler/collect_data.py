import copy
import logging

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from driver.services import RouteService as DriverRouteService
from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.pickup import PickupJobStatusChoices
from opv2.services import PickupService
from stos.utils import configs, chunk_list, check_record_change, parse_datetime
from ..models import PickupJob, PickupJobOrder

logger = logging.getLogger(__name__)


def collect_job_data():
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_BI')),
        spreadsheet_id=configs.get('PUJ_SPREADSHEET_ID'),
        logger=logger
    )

    # Get all records from the Google Sheet
    records = gsheet_service.get_all_records(configs.get('PUJ_WORKSHEET_ID', cast=int))

    # Check if records exist
    if not records:
        logger.info('No records found in Google Sheet, skipping processing.')
        return
    total_records = len(records)
    success_records = 0
    for chunk in chunk_list(records, 1000):
        job_ids = [row.get('pickup_job_id') for row in chunk]

        # Get existing records to avoid duplicates
        existing_job_ids = set(
            PickupJob.objects.filter(
                job_id__in=job_ids
            ).values_list('job_id', flat=True)
        )

        new_records = []
        for index, row in enumerate(chunk):
            job_id = row.get('job_id')

            # Skip if record already exists
            if job_id in existing_job_ids:
                continue

            try:
                new_records.append(PickupJob(
                    job_id=job_id,
                    shipper_id=row.get('global_shipper_id'),
                    shipper_name=row.get('shipper'),
                    contact=row.get('contact'),
                    pickup_schedule_date=parse_datetime(row.get('schedule_pickup_datetime')),
                    shipper_address=row.get('pickup_address'),
                    call_center_status=row.get('call_center_status'),
                    call_center_sent_time=parse_datetime(row.get('call_center_sent_time')),
                ))
            except Exception as e:
                logger.error(f"Failed to process row {index + 1}: {e}")

        # Bulk create new records
        if new_records:
            success = bulk_create_with_history(new_records, PickupJob, batch_size=1000, ignore_conflicts=True)
            logger.info(f"Successfully processed {len(success)} records.")
            success_records += len(success)
        else:
            logger.info("No new records to process.")

    logger.info(f"Processed {success_records}/{total_records} records.")


def collect_job_info():
    pickup_jobs = PickupJob.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        (
                Q(status__isnull=True) |
                ~Q(status__in=[PickupJobStatusChoices.FAILED, PickupJobStatusChoices.COMPLETED,
                               PickupJobStatusChoices.NO_POP, PickupJobStatusChoices.CANCELLED])
        )
    )

    if not pickup_jobs.exists():
        logger.info("No data to update")
        return

    # Initialize PickupService
    pickup_service = PickupService(logger=logger)

    stt_code, response = pickup_service.get_info(pickup_jobs)

    if stt_code != 200:
        logger.error(f"Failed to get job info: {response}")
        return

    map_waypoint = {jb['pickup_appointment_job_id']: jb['waypoint_id'] for jb in response['data']}
    map_status = {jb['pickup_appointment_job_id']: jb['status'] for jb in response['data']}
    map_driver_id = {jb['pickup_appointment_job_id']: jb['driver_id'] for jb in response['data']}

    update_data = []
    for pickup_job in pickup_jobs:
        new_pickup_job = copy.deepcopy(pickup_job)
        new_pickup_job.waypoint_id = map_waypoint.get(pickup_job.job_id)
        new_pickup_job.driver_id = map_driver_id.get(pickup_job.job_id)
        new_pickup_job.status = map_status.get(pickup_job.job_id)
        new_pickup_job.updated_date = timezone.now()

        is_updated, existing_record, _ = check_record_change(
            existing_record=pickup_job,
            updated_record=new_pickup_job,
            excluded_fields=['tracking_id', 'order_sn']
        )
        if is_updated:
            update_data.append(existing_record)

    try:
        success = bulk_update_with_history(update_data, PickupJob, ['waypoint_id', 'status', 'updated_date', 'driver_id'], batch_size=1000)
        logger.info(f"Successfully updated {success} records.")
    except Exception as e:
        logger.error(f"Failed to update records: {e}")


def collect_packets():
    driver_route_service = DriverRouteService(logger=logger)
    stt_code, response = driver_route_service.fetch_route()

    if stt_code != 200:
        logger.error(f"Failed to get route info: {response}")
        raise Exception(f"Failed to get route info: {response}")

    orders_to_create = []

    for route in response['data']['routes']:
        for waypoint in route['waypoints']:
            for job in waypoint['jobs']:
                try:
                    job_instance = PickupJob.objects.get(pk=job['id'])
                except PickupJob.DoesNotExist:
                    logger.error(f"PickupJob with id {job['id']} does not exist.")
                    continue
                for parcel in job['parcels']:
                    orders_to_create.append(
                        PickupJobOrder(
                            order_id=parcel['id'],
                            job_id=job_instance,
                            tracking_id=parcel['tracking_id'],
                            parcel_size=parcel['parcel_size']
                        )
                    )

    if orders_to_create:
        success = bulk_create_with_history(orders_to_create, PickupJobOrder, batch_size=1000, ignore_conflicts=True)
        logger.info(f"Successfully created {len(success)} records.")
    else:
        logger.info("No records to create.")
