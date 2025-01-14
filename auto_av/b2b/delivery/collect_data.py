import logging

from django.db.models import Q
from django.db.models.functions import Lower
from simple_history.utils import bulk_create_with_history

from network.models import Zone
from opv2.models import ShipperB2B
from opv2.services import OrderService
from ...models import OrderB2B, StageChoices

logger = logging.getLogger(__name__)


def collect_order_av_to_b2b_lm():
    # Get all shipper b2b ids
    shipper_b2b_ids = list(ShipperB2B.objects.values_list('shipper_id', flat=True))

    order_service = OrderService(logger)

    stt_code, orders = order_service.parcel_address_search(shipper_b2b_ids, df=True)

    if stt_code != 200:
        logger.error(f"Error when get parcel address search: {orders}")
        return

    logger.info(f"Got {len(orders)} orders")

    # Get all zones b2b
    zone_ids = list(Zone.objects.annotate(
        name_lower=Lower('name')
    ).filter(
        name_lower__icontains='b2b'
    ).values_list('id', flat=True))
    logger.info(f"Have {len(zone_ids)} zones b2b")

    orders = orders[~orders['zone_id'].isin(zone_ids)].reset_index(drop=True)

    # Filter not hub VIET (ID: 1)
    orders = orders[orders['hub_id'] != 1].reset_index(drop=True)

    logger.info(f"Filtered {len(orders)} orders")

    exiting_records = list(OrderB2B.objects.filter(
        Q(tracking_id__in=orders['tracking_id'].tolist())
        & Q(stage__in=[StageChoices.IN_QUEUE, StageChoices.NOT_VERIFIED, StageChoices.B2B_LM_AV])
    ).values_list('tracking_id', flat=True).distinct())

    new_records = []
    for index, order in orders.iterrows():
        try:
            tracking_id = order['tracking_id']
            if tracking_id in exiting_records:
                logger.info(f"Order {tracking_id} is already in the system.")
                continue
            order_b2b = OrderB2B(
                tracking_id=order['tracking_id'],
                order_id=order['order_id'],
                shipper_id=order['global_shipper_id'],
                waypoint=order['waypoint_id'],
                address=f"{order['address_one']} {order['address_two']}",
                zone_id=order['zone_id'],
                hub_id=order['hub_id'],
            )
            new_records.append(order_b2b)
        except Exception as e:
            logger.error(f"Error when create order b2b: {e}")
            continue

    try:
        created = bulk_create_with_history(new_records, OrderB2B, batch_size=1000, ignore_conflicts=True)
        logger.info(f"Created {len(created)} new Order B2B records.")
    except Exception as e:
        logger.error(f"Error when create order b2b: {e}")
        return
