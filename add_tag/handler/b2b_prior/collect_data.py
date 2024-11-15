import logging

from simple_history.utils import bulk_create_with_history

from redash.client import RedashClient
from stos.utils import configs, chunk_list
from ...models import PriorB2B

logger = logging.getLogger(__name__)


def collect_data_from_redash():
    redash_client = RedashClient(
        api_key=configs.get('REDASH_API_KEY'),
        logger=logger
    )

    try:
        data = redash_client.fresh_query_result(2244)
    except Exception as e:
        raise e

    total_data = len(data)
    total_success = 0
    for chunk in chunk_list(data, 1000):
        news = []
        for order in chunk:
            try:
                news.append(PriorB2B(
                    order_id=order.get('order_id'),
                    tracking_id=order.get('tracking_id'),
                    granular_status=order.get('granular_status'),
                    shipper_id=order.get('global_shipper_id'),
                    shipper_name=order.get('shipper_name'),
                    curr_zone_name=order.get('curr_zone_name'),
                    creation_datetime=order.get('creation_datetime'),
                    pickup_datetime=order.get('pickup_datetime'),
                    pickup_hub_name=order.get('pickup_hub_name'),
                    delivery_hub_name=order.get('delivery_hub_name'),
                    route=order.get('route'),
                    date_to_prior=order.get('date_to_prior'),
                ))
            except Exception as e:
                logger.error(f"Error creating order {order['tracking_id']}: {e}")
                continue

        success = bulk_create_with_history(news, PriorB2B, batch_size=1000, ignore_conflicts=True)
        total_success += len(success)

    logger.info(f"Succeed to collect {total_success} out of {total_data} data from Redash")
