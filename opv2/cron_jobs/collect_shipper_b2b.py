import logging

from celery import shared_task
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from core.base.task import STOsQueueOnce
from stos.utils import check_record_change
from ..models import ShipperB2B
from ..services import ShipperService

logger = logging.getLogger(__name__)


@shared_task(name='[Cron Job] Collect Shipper B2B', base=STOsQueueOnce, once={'graceful': True})
def collect_shipper_b2b():
    shipper_svc = ShipperService(logger)

    # Get all shippers B2B
    status_code, shippers = shipper_svc.shipper_search('CORP_B2B')

    if status_code != 200:
        logger.error(f'Failed to get shippers B2B. Status code: {status_code}')
        return

    shipper_ids = [shipper.id for shipper in shippers]

    existing_records = ShipperB2B.objects.filter(shipper_id__in=shipper_ids)
    existing_records_map = {f'{record.shipper_id}': record for record in existing_records}

    total_opv2_shippers = len(shippers)
    total_changed_shippers = 0
    new_records, update_records = [], []

    # region Process Changes
    for shipper in shippers:
        try:
            record = ShipperB2B(
                shipper_id=shipper.id,
                shipper_name=shipper.name
            )
        except Exception as e:
            logger.error(f'Failed to create record for shipper {shipper.id}. Error: {e}')
            continue

        existing_record = existing_records_map.get(f'{shipper.id}')
        if existing_record:
            is_change, record, _ = check_record_change(existing_record, record, )
            if is_change:
                update_records.append(record)
        else:
            new_records.append(record)
    # endregion

    # region Save Changes
    try:
        if new_records:
            created = bulk_create_with_history(new_records, ShipperB2B, batch_size=1000, ignore_conflicts=True)
            total_changed_shippers += len(created)
            logger.info(f'Created {len(created)} new Shipper B2B records.')
        else:
            logger.info('No new Shipper B2B records to create.')
    except Exception as e:
        logger.error(f'Failed to update new Shipper B2B records. Error: {e}')

    try:
        if update_records:
            updated = bulk_update_with_history(update_records, ShipperB2B, batch_size=1000, fields=['shipper_name'])
            total_changed_shippers += updated
            logger.info(f'Updated {updated} Shipper B2B records.')
        else:
            logger.info('No Shipper B2B records to update.')
    except Exception as e:
        logger.error(f'Failed to update Shipper B2B records. Error: {e}')
    # endregion

    logger.info(
        f'Finished collecting Shipper B2B. Total OPv2 shippers: {total_opv2_shippers}. Total changed shippers: {total_changed_shippers}')
