import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from opv2.base.order import TagChoices
from opv2.base.ticket import TicketTypeChoices
from opv2.dto import TicketCreateDTO
from opv2.services import TicketService, OrderService
from ..models import Order

logger = logging.getLogger(__name__)


def create_cs_ticket():
    # get all orders
    orders = Order.objects.filter(
        Q(cs_created_at__isnull=True) &
        Q(changed_address_at__isnull=True)
    )

    if not orders.exists():
        logger.info("No orders found.")
        return

    ticket_service = TicketService(logger=logger)

    data = [
        TicketCreateDTO(
            tracking_id=order.tracking_id,
            type=TicketTypeChoices.SELF_COLLECTION,
            sub_type=None,
            investigating_hub_id=12,
            investigating_group='FLT-LM',
            ticket_notes='STOs create for Shein RTS',
            assignee_email=None
        ) for order in orders
    ]

    stt_code, result = ticket_service.create_tickets(data)

    if stt_code != 200:
        logger.error("Failed to create CS ticket.")
        return

    success = result.get('success', [])
    failed = result.get('failed', [])

    logger.info(f"Successfully created CS ticket. Success: {success}, Failed: {failed}")

    try:
        with transaction.atomic():
            orders.update(cs_created_at=timezone.now())
        logger.info("Successfully created CS ticket.")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def change_address():
    orders = Order.objects.filter(
        Q(changed_address_at__isnull=True)
    )

    if not orders.exists():
        logger.info("No orders found.")
        return

    order_service = OrderService(logger=logger)

    for order in orders:
        stt_code, data = order_service.change_to_address(
            order_id=order.order_id,
            address1='117/2D3B Hồ Văn Long, Phường Tân Tạo, Quận Bình Tân, TP. HCM',
            address2='',
            city='',
        )

        if stt_code != 200:
            logger.error(f"Failed to change address for order {order.order_id}")
            continue

        try:
            with transaction.atomic():
                order.update(changed_address_at=timezone.now())
            logger.info("Successfully change address ticket.")
        except Exception as e:
            logger.error(f"Failed to update orders: {e}")
            raise e


def add_tag():
    orders = Order.objects.filter(
        Q(added_tag_at__isnull=True)
    )

    if not orders.exists():
        logger.info("No orders found.")
        return

    order_service = OrderService(logger=logger)

    stt_code, result = order_service.add_tags(
        order_ids=[order.order_id for order in orders],
        tags=[TagChoices.RTS_SHEIN]
    )

    if stt_code != 200:
        logger.error("Failed to add tag.")
        return

    success = result.get('success', [])
    failed = result.get('failed', [])
    logger.info(f"Successfully added tag. Success: {success}, Failed: {failed}")

    try:
        with transaction.atomic():
            orders.update(added_tag_at=timezone.now())
        logger.info("Successfully add tag ticket.")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e
