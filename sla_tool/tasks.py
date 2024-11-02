from celery import shared_task, chain

from core.base.task import STOsTask
from .handler.caculate_sla import (
    calculate_sla_date_shopee,
    calculate_sla_date_tiktok
)
from .handler.need_call import (
    out_to_stos_sheet,
    out_to_bi_sheet,
)
from .handler.shopee import (
    collect_shopee_backlogs,
    update_shopee_order_info_form_opv2
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


@shared_task(name='[SLA Tool] collect_call_data_task', base=STOsTask, once={'graceful': True})
def collect_call_data_task(*args, **kwargs):
    collect_breach_sla_call()
    collect_record_call()


# region Shopee
@shared_task(name='[SLA Tool] collect_shopee_backlogs_task', base=STOsTask, once={'graceful': True})
def collect_shopee_backlogs_task(*args, **kwargs):
    collect_shopee_backlogs()


@shared_task(name='[SLA Tool] collect_shopee_extend_sla_task', base=STOsTask, once={'graceful': True})
def collect_shopee_extend_sla_task(*args, **kwargs):
    collect_extend_sla()


@shared_task(name='[SLA Tool] calculate_shopee_sla_date_task', base=STOsTask, once={'graceful': True})
def calculate_shopee_sla_date_task(*args, **kwargs):
    calculate_sla_date_shopee()


@shared_task(name='[SLA Tool] load_shopee_order_info_task', base=STOsTask, once={'graceful': True})
def load_shopee_order_info_task(*args, **kwargs):
    update_shopee_order_info_form_opv2()


# endregion

# region TikTok
@shared_task(name='[SLA Tool] collect_tiktok_backlogs_task', base=STOsTask, once={'graceful': True})
def collect_tiktok_backlogs_task(*args, **kwargs):
    collect_tiktok_backlogs()


@shared_task(name='[SLA Tool] calculate_tiktok_sla_date_task', base=STOsTask, once={'graceful': True})
def calculate_tiktok_sla_date_task(*args, **kwargs):
    calculate_sla_date_tiktok()


@shared_task(name='[SLA Tool] load_tiktok_order_info_task', base=STOsTask, once={'graceful': True})
def load_tiktok_order_info_task(*args, **kwargs):
    update_tiktok_order_info_form_opv2()


# endregion

@shared_task(name='[SLA Tool] out_to_sheet_task', base=STOsTask, once={'graceful': True})
def out_to_sheet_task(*args, **kwargs):
    out_to_stos_sheet()
    out_to_bi_sheet()


@shared_task(name='[SLA Tool] get_need_call_tasks', base=STOsTask, once={'graceful': True})
def collect_all_data_task():
    return chain(
        collect_shopee_backlogs_task.s(),
        collect_tiktok_backlogs_task.s(),
        load_shopee_order_info_task.s(),
        load_tiktok_order_info_task.s(),
        out_to_sheet_task.s(),
    )()
