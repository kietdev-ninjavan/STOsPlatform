import logging

from django.db import transaction
from django.db.models import Q
from collections import OrderedDict
from network.models import Zone
from opv2.dto import BulkAVDTO
import fireducks.pandas as pd
from opv2.services import OrderService
from ...models import OrderB2B, StageChoices

logger = logging.getLogger(__name__)


def update_order_info():
    orders = OrderB2B.objects.filter(
        Q(stage=StageChoices.B2B_AV)
        & Q(granular_status__isnull=True)
    )

    if not orders.exists():
        logger.info("No orders to update")
        return

    order_svc = OrderService(logger)

    stt_code, result = order_svc.search_all(orders.values_list('tracking_id', flat=True))

    if stt_code != 200:
        logger.error(f"Error when get parcel address search: {result}")
        return
    update = []
    for order in orders:
        order_info = result.get(order.tracking_id)

        if order_info:
            order.granular_status = order_info.granular_status
            order.status = order_info.status
            order.rts = order_info.is_rts
            order.mps_id = order_info.mps_id
            order.mps_sequence_number = order_info.mps_sequence_number
            update.append(order)
        else:
            logger.error(f"Order {order.tracking_id} not found in search result")

    try:
        with transaction.atomic():
            OrderB2B.objects.bulk_update(update, ['granular_status', 'status', 'rts', 'mps_id', 'mps_sequence_number'])
    except Exception as e:
        logger.error(f"Error when updating order info: {e}")


def __get_first_dws(data):
    df = pd.DataFrame(data)

    # Filter DWS
    df = df[(df['type'] == 'HUB_INBOUND_SCAN') & (df['user_grant_type'] == 'CLIENT_CREDENTIALS')].reset_index(drop=True)

    if df.empty:
        return None

    # First DWS
    parcel_size_id = (df['data'][0]).get('parcel_size_id').get('new_value')

    return parcel_size_id


def update_parcel_size():
    orders = OrderB2B.objects.filter(
        Q(stage=StageChoices.B2B_AV)
        & ~Q(shipper_id__in=[10180487])
        & Q(mps_sequence_number=1)
        & Q(parcel_size__isnull=True)
    )

    if not orders.exists():
        logger.info("No orders to update")
        return

    order_svc = OrderService(logger)
    for order in orders:
        stt_code, result = order_svc.get_events(order.order_id)

        if stt_code != 200:
            logger.error(f"Error when get order history: {result}")
            continue

        parcel_size_id = __get_first_dws(result)

        if parcel_size_id:
            order.parcel_size = parcel_size_id
            order.save()
        else:
            logger.error(f"Order {order.tracking_id} not found DWS")

def __get_zone_njv_coordinates(zone_id):
    try:
        # Fetch the Hub object by its ID
        hub = Zone.objects.get(id=zone_id)
        latitude = hub.latitude
        longitude = hub.longitude
        return latitude, longitude
    except Zone.DoesNotExist:
        return None, None


def address_verification_to_njv_lm():
    orders = OrderB2B.objects.filter(
        Q(stage=StageChoices.B2B_AV)
        & ~Q(shipper_id__in=[10180487])
        & Q(mps_sequence_number=1)
        & Q(parcel_size__in=[5,0,1,2])
    )

    if not orders.exists():
        logger.info("No orders to verify")
        return

    logger.info(f"Got {orders.count()} orders to verify")

    # Distinct orders by waypoint
    unique_orders = list(OrderedDict((order.waypoint, order) for order in orders).values())
    logger.info(f"Got {len(unique_orders)} unique orders")

    # Begin a transaction to ensure atomic updates
    try:
        with transaction.atomic():
            # Update all orders' stage to 'IN_QUEUE'
            orders.update(stage=StageChoices.IN_QUEUE)

            update_info = []
            for order in unique_orders:
                # Get latitude and longitude from order
                latitude, longitude = __get_zone_njv_coordinates(order.zone_id)

                update_info.append(BulkAVDTO(
                    waypoint=order.waypoint,
                    latitude=latitude,
                    longitude=longitude,
                ))

                order_service = OrderService(logger)

                stt_code, result = order_service.bulk_update_av(update_info)

                if stt_code != 200:
                    logger.error(f"Error occurred when updating AV: {result}")
                    raise Exception("Error occurred when updating AV in OPv2")
    except Exception as e:
        logger.error(f"Error occurred while processing orders: {e}")
        raise e

    orders_failed = result.get('failed', [])
    orders_success = result.get('success', [])

    # Update the stage of the orders based on the result
    try:
        with transaction.atomic():
            OrderB2B.objects.filter(waypoint__in=orders_failed).update(stage=StageChoices.NOT_VERIFIED)
    except Exception as e:
        logger.error(f"Error when updating : {orders_failed}")
        logger.error(f"Error occurred while updating failed orders: {e}")
        raise e

    try:
        with transaction.atomic():
            OrderB2B.objects.filter(waypoint__in=orders_success).update(stage=StageChoices.B2B_LM_AV)
    except Exception as e:
        logger.error(f"Error when updating : {orders_success}")
        logger.error(f"Error occurred while updating success orders: {e}")
        raise e
