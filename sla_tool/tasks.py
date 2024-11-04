from celery import shared_task

from core.base.task import STOsTask
from .handler.calculate_sla import (
    calculate_sla_date_shopee,
    calculate_sla_date_tiktok
)
from .handler.final import (
    out_shopee_extended_date,
    out_breach_data
)
from .handler.need_call import (
    out_to_stos_sheet,
    out_to_bi_sheet,
)
from .handler.shopee import (
    collect_shopee_backlogs,
    update_shopee_order_info_form_opv2,
    create_shipper_date
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


@shared_task(name='[SLA Tool] Handle Collect Call Data', base=STOsTask, once={'graceful': True})
def collect_call_data_task():
    collect_breach_sla_call()
    collect_record_call()


@shared_task(name='[SLA Tool] Handle Calculate SLA', base=STOsTask, once={'graceful': True})
def collect_shopee_extend_sla_task():
    collect_extend_sla()
    calculate_sla_date_shopee()
    calculate_sla_date_tiktok()


@shared_task(name='[SLA Tool] Handle Find Missing Call', base=STOsTask, once={'graceful': True})
def find_missing_call_task():
    # Shopee
    collect_shopee_backlogs()
    create_shipper_date()
    update_shopee_order_info_form_opv2()

    # Tiktok
    collect_tiktok_backlogs()
    update_tiktok_order_info_form_opv2()

    # Output
    out_to_stos_sheet()
    out_to_bi_sheet()


@shared_task(name='[SLA Tool] Import Final Sheet', base=STOsTask, once={'graceful': True})
def import_final_sheet():
    out_shopee_extended_date()
    out_breach_data()
