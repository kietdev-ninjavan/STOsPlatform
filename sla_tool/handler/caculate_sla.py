import logging

from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from ..models import ShopeeBacklog, TiktokBacklog, ExtendSLATracking

logger = logging.getLogger(__name__)


def calculate_sla_date_shopee():
    """
    Calculate the SLA date for Shopee backlogs in bulk for better performance.
    """
    # Fetch all necessary ShopeeBacklog and ExtendSLATracking objects
    shopee_backlogs = ShopeeBacklog.objects.filter(aging_from_lost_threshold=0)

    # Fetch ExtendSLATracking and create a lookup dictionary by tracking_id
    extend_sla_tracking = ExtendSLATracking.objects.filter(
        tracking_id__in=shopee_backlogs.values_list('tracking_id', flat=True)
    )

    extend_sla_dict = {sla.tracking_id: sla for sla in extend_sla_tracking}

    update_list = []
    for backlog in shopee_backlogs:
        extend_sla = extend_sla_dict.get(backlog.tracking_id)
        if extend_sla:
            backlog.extend_days = extend_sla.extend_days
            backlog.extended_date = extend_sla.breach_sla_expectation
        else:
            backlog.extend_days = 0
            backlog.extended_date = timezone.now() + timezone.timedelta(days=1)
        update_list.append(backlog)

    # Perform a bulk update once after processing all records
    if update_list:
        success = bulk_update_with_history(update_list, ShopeeBacklog, ['extend_days', 'extended_date'])
        logger.info(f"Successfully updated {success}/{len(update_list)} Shopee backlogs with SLA information.")
    else:
        logger.info("No Shopee backlogs to update.")


def calculate_sla_date_tiktok():
    """
    Calculate the SLA date for Tiktok backlogs in bulk for better performance.
    """
    tiktok_backlogs = TiktokBacklog.objects.filter(extended_date__isnull=True)

    if not tiktok_backlogs.exists():
        logger.info("No Tiktok backlogs to update.")
        return

    update_list = []
    for backlog in tiktok_backlogs:
        backlog.extend_days = 2
        backlog.extended_date = backlog.date + timezone.timedelta(days=2)
        update_list.append(backlog)

    # Perform a bulk update once after processing all records
    if update_list:
        success = bulk_update_with_history(update_list, TiktokBacklog, ['extend_days', 'extended_date'])
        logger.info(f"Successfully updated {success}/{len(update_list)} Tiktok backlogs with SLA information.")
    else:
        logger.info("No Tiktok backlogs to update.")
