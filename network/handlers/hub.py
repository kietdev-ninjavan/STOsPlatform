import logging

from django.db import DatabaseError
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from opv2.services.network_service import NetworkService
from stos.utils import chunk_list, check_record_change
from ..models import Hub

logger = logging.getLogger(__name__)


def collect_hubs():
    logger.info("Collecting hubs from the API")
    nw_service = NetworkService(logger=logger)

    stt_code, hubs = nw_service.get_all_hubs()

    if stt_code != 200:
        logger.error("Failed to get hubs from the API")
        raise Exception("Failed to get hubs from the API")

    logger.info(f"Received {len(hubs)} hubs from the API")

    total_success = 0
    total_updated = 0
    for chunk in chunk_list(hubs, 1000):
        logger.info(f"Processing chunk of {len(chunk)} hubs")
        hub_ids = [hub.id for hub in chunk]

        existing_hubs = Hub.objects.filter(id__in=hub_ids)

        existing_hub_ids = {hub.id: hub for hub in existing_hubs}

        insert_data, update_data = [], []

        for hub in chunk:
            new_hub = Hub(
                id=hub.id,
                name=hub.name,
                country=hub.country,
                city=hub.city,
                latitude=hub.latitude,
                longitude=hub.longitude,
                region=hub.region,
                area=hub.area,
                active=hub.active,
                short_name=hub.short_name,
                sort_hub=hub.sort_hub,
                facility_type=hub.facility_type,
                opv2_created_at=hub.opv2_created_at,
                opv2_updated_at=hub.opv2_updated_at,
                virtual_hub=hub.virtual_hub,
                parent_hub=hub.parent_hub
            )

            existing_record = existing_hub_ids.get(hub.id)
            if existing_record:
                is_updated, existing_record, _ = check_record_change(
                    existing_record=existing_record,
                    updated_record=new_hub,
                )

                if is_updated:
                    update_data.append(existing_record)
            else:
                insert_data.append(new_hub)

        try:
            if insert_data:
                created_records = bulk_create_with_history(
                    insert_data,
                    Hub,
                    ignore_conflicts=True,
                    batch_size=1000
                )
                total_success += len(created_records)
                logger.info(f'Inserted {len(created_records)} new hub records.')
            else:
                logger.info('No new records to insert.')

            if update_data:
                updated_count = bulk_update_with_history(
                    update_data,
                    Hub,
                    fields=[
                        'name', 'country', 'city', 'latitude', 'longitude', 'region', 'area', 'active', 'short_name',
                        'sort_hub', 'facility_type', 'opv2_created_at', 'opv2_updated_at', 'virtual_hub', 'parent_hub'
                    ],
                    batch_size=1000
                )
                total_updated += updated_count
                logger.info(f'Updated {updated_count} Hub records.')
            else:
                logger.info('No records to update.')

        except (DatabaseError, Exception) as e:
            logger.error(f'Error during bulk operations: {e}')
            continue

    logger.info(f"Total success: {total_success}, Total updated: {total_updated}")
