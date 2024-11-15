import logging

from django.db.models import Q
from django.utils import timezone

from opv2.base.order import TagChoices
from opv2.services import OrderService
from .report import report_add_tag
from ...models import PriorB2B

logger = logging.getLogger(__name__)


def add_tag():
    orders = PriorB2B.objects.filter(
        Q(created_date__date=timezone.now().date())
    )

    if not orders.exists():
        logger.info("No orders need to add tag")
        return

    # init order service
    order_service = OrderService(logger=logger)

    stt_code, result = order_service.add_tags(
        order_ids=[order.order_id for order in orders],
        tags=[TagChoices.PRIOR]
    )

    if stt_code != 200:
        logger.error(f"Error adding tag: {result}")
        raise Exception("Error adding tag.")

    success = result.get("success", [])
    failed = result.get("failed", [])

    logger.info("Tag added successfully.")

    report_add_tag(len(orders), len(success), failed)
