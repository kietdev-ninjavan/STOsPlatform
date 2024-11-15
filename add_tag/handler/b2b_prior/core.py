import logging

from django.db.models import Q
from django.utils import timezone

from opv2.base.order import TagChoices
from opv2.services import OrderService
from .output import out_to_sheet
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

    try:
        report_add_tag(len(orders), len(success), failed)
    except Exception as e:
        logger.error(f"Error while reporting: {e}")

    try:
        out_to_sheet([order.tracking_id for order in orders if order.order_id in success])
    except Exception as e:
        logger.error(f"Error while output to sheet: {e}")
