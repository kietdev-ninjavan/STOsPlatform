from celery import shared_task

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


@shared_task(name='collect_call_data_task', base=STOsTask)
def collect_call_data_task():
    collect_breach_sla_call()
    collect_record_call()


# region Shopee
@shared_task(name='collect_shopee_backlogs_task', base=STOsTask)
def collect_shopee_backlogs_task():
    collect_shopee_backlogs()


@shared_task(name='collect_shopee_extend_sla_task', base=STOsTask)
def collect_shopee_extend_sla_task():
    collect_extend_sla()


@shared_task(name='calculate_shopee_sla_date_task', base=STOsTask)
def calculate_shopee_sla_date_task():
    calculate_sla_date_shopee()


@shared_task(name='load_shopee_order_info_task', base=STOsTask)
def load_shopee_order_info_task():
    update_shopee_order_info_form_opv2()


# endregion

# region TikTok
@shared_task(name='collect_tiktok_backlogs_task', base=STOsTask)
def collect_tiktok_backlogs_task():
    collect_tiktok_backlogs()


@shared_task(name='calculate_tiktok_sla_date_task', base=STOsTask)
def calculate_tiktok_sla_date_task():
    calculate_sla_date_tiktok()


@shared_task(name='load_tiktok_order_info_task', base=STOsTask)
def load_tiktok_order_info_task():
    update_tiktok_order_info_form_opv2()


# endregion

@shared_task(name='out_to_sheet_task', base=STOsTask)
def out_to_sheet_task():
    out_to_stos_sheet()
    out_to_bi_sheet()
