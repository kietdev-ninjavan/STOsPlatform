import logging
from collections import OrderedDict

from django.db import transaction

from network.models import Hub
from opv2.dto import BulkAVDTO
from opv2.services import OrderService
from ...models import OrderB2B, StageChoices

logger = logging.getLogger(__name__)


def __get_hub_b2b_coordinates(hub_id):
    try:
        # Fetch the Hub object by its ID
        hub = Hub.objects.get(id=hub_id)

        # Check if the hub has a related HubB2B object
        if hub.b2b_hub:
            latitude = hub.b2b_hub.latitude
            longitude = hub.b2b_hub.longitude
            return latitude, longitude
        else:
            return None, None
    except Hub.DoesNotExist:
        return None, None


def address_verification_to_b2b_lm():
    # Get all orders that are not verified
    orders = OrderB2B.objects.filter(stage=StageChoices.NOT_VERIFIED)

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
                latitude, longitude = __get_hub_b2b_coordinates(order.hub_id)

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
            OrderB2B.objects.filter(waypoint__in=orders_success).update(stage=StageChoices.B2B_AV)
    except Exception as e:
        logger.error(f"Error when updating : {orders_success}")
        logger.error(f"Error occurred while updating success orders: {e}")
        raise e
