import logging

from django.db import DatabaseError
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from opv2.services.network_service import NetworkService
from stos.utils import chunk_list, check_record_change
from ..models import Zone

logger = logging.getLogger(__name__)


def collect_zones():
    logger.info("Collecting zones from the API")
    nw_service = NetworkService(logger=logger)

    stt_code, zones = nw_service.get_all_zones()

    if stt_code != 200:
        logger.error("Failed to get zones from the API")
        raise Exception("Failed to get zones from the API")

    logger.info(f"Received {len(zones)} zones from the API")

    total_success = 0
    total_updated = 0
    for chunk in chunk_list(zones, 1000):
        logger.info(f"Processing chunk of {len(chunk)} zones")
        zone_ids = [zone.id for zone in chunk]

        existing_zones = Zone.objects.filter(id__in=zone_ids)

        existing_zone_ids = {zone.id: zone for zone in existing_zones}

        insert_data, update_data = [], []

        for zone in chunk:
            new_zone = Zone(
                id=zone.id,
                legacy_zone_id=zone.legacy_zone_id,
                name=zone.name,
                type=zone.type,
                hub_id=zone.hub_id,
                short_name=zone.short_name,
                description=zone.description,
                latitude=zone.latitude,
                longitude=zone.longitude,
            )

            existing_record = existing_zone_ids.get(zone.id)
            if existing_record:
                is_updated, existing_record, _ = check_record_change(
                    existing_record=existing_record,
                    updated_record=new_zone,
                )

                if is_updated:
                    update_data.append(existing_record)
            else:
                insert_data.append(new_zone)

        try:
            if insert_data:
                created_records = bulk_create_with_history(
                    insert_data,
                    Zone,
                    ignore_conflicts=True,
                    batch_size=1000
                )
                total_success += len(created_records)
                logger.info(f'Inserted {len(created_records)} new Zone records.')
            else:
                logger.info('No new records to insert.')

            if update_data:
                updated_count = bulk_update_with_history(
                    update_data,
                    Zone,
                    fields=[
                        'legacy_zone_id', 'name', 'type', 'hub_id', 'short_name', 'description',
                        'latitude', 'longitude', 'updated_date'
                    ],
                    batch_size=1000
                )
                total_updated += updated_count
                logger.info(f'Updated {updated_count} Zone records.')
            else:
                logger.info('No records to update.')

        except (DatabaseError, Exception) as e:
            logger.error(f'Error during bulk operations: {e}')
            continue

    logger.info(f"Total success: {total_success}, Total updated: {total_updated}")
