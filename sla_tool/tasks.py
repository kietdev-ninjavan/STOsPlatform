from celery import shared_task
from django.utils import timezone

from core.base.task import STOsQueueOnce
from .handler.calculate_sla import (
    calculate_sla_date_shopee,
    calculate_sla_date_tiktok
)
from .handler.final import (
    out_shopee_extended_date,
    out_breach_data
)
from .handler.need_call import (
    out_zns_to_bi
)
from .handler.shopee import (
    collect_shopee_backlogs,
    update_shopee_order_info_form_opv2,
    create_shipper_date,
    create_zns_date
)
from .handler.sla_call import (
    collect_breach_sla_call,
    collect_record_call
)
from .handler.sla_extend import collect_extend_sla
from .handler.tiktok import (
    collect_tiktok_backlogs,
    update_tiktok_order_info_form_opv2
)


@shared_task(name='[SLA Tool] Handle Collect Call Data', base=STOsQueueOnce, once={'graceful': True})
def collect_call_data_task():
    collect_breach_sla_call()
    collect_record_call()


@shared_task(name='[SLA Tool] Handle Calculate SLA', base=STOsQueueOnce, once={'graceful': True})
def collect_shopee_extend_sla_task():
    collect_extend_sla()
    calculate_sla_date_shopee()
    calculate_sla_date_tiktok()


@shared_task(name='[SLA Tool] Handle Find ZNS', base=STOsQueueOnce, once={'graceful': True})
def find_zns():
    # Shopee
    collect_shopee_backlogs()
    create_shipper_date()
    create_zns_date()
    update_shopee_order_info_form_opv2()

    # Tiktok
    update_tiktok_order_info_form_opv2(timezone.now().date() + timezone.timedelta(days=1))

    # Out to BI Sheet
    out_zns_to_bi()


@shared_task(name='[SLA Tool] Handle Find Missing Call', base=STOsQueueOnce, once={'graceful': True})
def find_missing_call_task():
    # Tiktok
    collect_tiktok_backlogs()
    update_tiktok_order_info_form_opv2(timezone.now().date())


@shared_task(name='[SLA Tool] Import Final Sheet', base=STOsQueueOnce, once={'graceful': True})
def import_final_sheet():
    out_shopee_extended_date()
    out_breach_data()
