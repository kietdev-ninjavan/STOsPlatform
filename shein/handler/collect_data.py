import logging

from simple_history.utils import bulk_create_with_history

from opv2.dto import AllOrderSearchFilterDTO
from opv2.services import OrderService
from stos.utils import chunk_dict
from ..models import Order

logger = logging.getLogger(__name__)


def collect_order_data():
    order_service = OrderService(logger=logger)

    # Get all orders
    search_filters = [
        AllOrderSearchFilterDTO(field='is_rts', values=[True]),
        AllOrderSearchFilterDTO(field="status", values=["Staging", "Pending", "Transit", "Pickup fail", "Delivery fail", "On Hold"])
    ]

    stt_code, data = order_service.search_all(data=[7512979], filter_by_shipper=True, search_filters=search_filters)
    if stt_code != 200:
        logger.error(f"Failed to get orders: {data}")
        return

    for chunk in chunk_dict(data, 1000):
        new_orders = []
        total_new = 0
        # get order existing in database
        existing_orders = Order.objects.filter(tracking_id__in=list(chunk.keys())).values_list('tracking_id', flat=True)

        for tracking_id, order in chunk.items():
            if tracking_id in existing_orders:
                continue

            new_orders.append(
                Order(
                    tracking_id=order.tracking_id,
                    order_id=order.id,
                    granular_status=order.granular_status,
                    status=order.status,
                    rts=order.is_rts
                )
            )

        try:
            success = bulk_create_with_history(new_orders, Order, batch_size=1000, ignore_conflicts=True)
            logger.info(f"Inserted {len(success)} new orders")
            total_new += len(success)
        except Exception as e:
            logger.error(f"Failed to create orders: {e}")
            continue

    logger.info(f"Total new orders: {total_new}")
