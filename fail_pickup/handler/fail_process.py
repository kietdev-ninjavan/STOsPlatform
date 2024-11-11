import logging
from typing import List

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from core.base.task import STOsParallel
from driver.services import UploadService, PickupService
from opv2.base.pickup import PickupJobStatusChoices
from stos.utils import create_zns_image, chunk_list
from ..models import PickupJob

logger = logging.getLogger(__name__)


def __make_physical_items(orders, reason_id, shipper_id):
    physical_items = []
    for order in orders:
        physical_item = {
            "action": "FAIL",
            "allow_reschedule": False,
            "failure_reason_id": reason_id,
            "global_shipper_id": shipper_id,
            "id": order.order_id,
            "parcel_size": order.parcel_size,
            "rts": False,
            "status": "Pending Pickup",
            "tracking_id": order.tracking_id
        }
        physical_items.append(physical_item)
    return physical_items


@shared_task(base=STOsParallel, name='[Fail Pickup] Fail Pickup Jobs')
def fail_job_task(job_ids: List[int] = None, reason_id: int = None):
    if not job_ids or not reason_id:
        return
        # Init Driver Service
    upload_service = UploadService()
    pickup_service = PickupService()

    jobs = PickupJob.objects.filter(job_id__in=job_ids)
    success = 0

    for job in jobs:
        # Make ZNS Image
        zns_info = {
            "Shipper name": f'{job.shipper_name}',
            "Shipper address": f'{job.shipper_address}',
            "Shipper contact": f'{job.contact}',
            "Call center status": f'{job.call_center_status}',
            "Call center sent time": f'{job.call_center_sent_time.strftime("%d/%m/%Y %H:%M:%S")}',
            "Schedule PU date": f'{job.pickup_schedule_date.strftime("%d/%m/%Y")}',
        }
        zns_image = create_zns_image(zns_info)

        # Upload ZNS Image
        stt_code, photo_response = upload_service.upload_photo(job.route.route_id, job.waypoint_id, content=zns_image)
        if stt_code != 200:
            logger.error(f"Failed to upload photo: {photo_response}")
            continue

        file_path = photo_response['data'].get('file_path')
        photo_url = photo_response['data'].get('url')

        # Make Physical Items
        physical_items = __make_physical_items(job.packets.all(), reason_id, job.shipper_id)

        # Fail Job
        stt_code, response = pickup_service.pickup_fail(
            route_id=job.route.route_id,
            waypoint_id=job.waypoint_id,
            contact=job.contact,
            file_path=file_path,
            photo_url=photo_url,
            failure_reason_id=reason_id,
            shipper_id=job.shipper_id,
            job_id=job.job_id,
            physical_items=physical_items
        )

        if stt_code != 200:
            logger.error(f"Failed to fail pickup job {job.job_id}: {response}")
            continue

        success += 1

    logger.info(f"Successfully processed {success}/{len(jobs)} records.")
    if success == 0:
        raise Exception('No job was failed')


def fail_job_kll():
    pickup_jobs = PickupJob.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(route_id__isnull=False) &
        Q(status=PickupJobStatusChoices.IN_PROGRESS) &
        Q(call_center_status='Fail') &
        Q(driver_id=1682343)
    )

    if not pickup_jobs.exists():
        logger.info('No jobs KLL found for fail')
        return

    for chunk in chunk_list(pickup_jobs, 1000):
        job_ids = [job.job_id for job in chunk]
        fail_job_task.delay(job_ids, 2711)


def fail_job_sh():
    pickup_jobs = PickupJob.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(route_id__isnull=False) &
        Q(status=PickupJobStatusChoices.IN_PROGRESS) &
        Q(call_center_status='Success') &
        Q(driver_id=1682343)
    )

    if not pickup_jobs.exists():
        logger.info('No jobs SH found for fail')
        return

    for chunk in chunk_list(pickup_jobs, 1000):
        job_ids = [job.job_id for job in chunk]
        fail_job_task.delay(job_ids, 2550)
