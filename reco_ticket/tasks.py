from celery import shared_task, chain

from core.base.task import STOsTask
from .handler.change_address.approve import (
    approve_hcm_dn_hn,
    approve_map_2_level
)
from .handler.change_address.collect_data import (
    collect_ticket_change_address,
    load_order_info
)
from .handler.change_address.manual import manual_ticket_have_alo_link
from .handler.change_address.resolve import (
    resolved_rts_and_last_status,
    resolved_ticket_system_create,
    resolved_ticket_storage_max_stored,
    resolved_have_changed_address,
    resolved_ticket_tokgistics,
    resolved_ticket_incorrect_format
)


@shared_task(name='[Change Address] collect_ticket_change_address_task', base=STOsTask)
def collect_ticket_change_address_task(*args, **kwargs):
    collect_ticket_change_address()


@shared_task(name='[Change Address] manual_ticket_have_alo_link_task', base=STOsTask)
def manual_ticket_have_alo_link_task(*args, **kwargs):
    manual_ticket_have_alo_link()


@shared_task(name='[Change Address] load_order_info_task', base=STOsTask)
def load_order_info_task(*args, **kwargs):
    load_order_info()


@shared_task(name='[Change Address] resolved_rts_and_last_status_task', base=STOsTask)
def resolved_rts_and_last_status_task(*args, **kwargs):
    resolved_rts_and_last_status()


@shared_task(name='[Change Address] resolved_ticket_system_create_task', base=STOsTask)
def resolved_ticket_system_create_task(*args, **kwargs):
    resolved_ticket_system_create()


@shared_task(name='[Change Address] resolved_ticket_storage_max_stored_task', base=STOsTask)
def resolved_ticket_storage_max_stored_task(*args, **kwargs):
    resolved_ticket_storage_max_stored()


@shared_task(name='[Change Address] resolved_have_changed_address_task', base=STOsTask)
def resolved_have_changed_address_task(*args, **kwargs):
    resolved_have_changed_address()


@shared_task(name='[Change Address] resolved_ticket_tokgistics_task', base=STOsTask)
def resolved_ticket_tokgistics_task(*args, **kwargs):
    resolved_ticket_tokgistics()


@shared_task(name='[Change Address] approve_hcm_dn_hn_task', base=STOsTask)
def approve_hcm_dn_hn_task(*args, **kwargs):
    approve_hcm_dn_hn()


@shared_task(name='[Change Address] approve_map_2_level_task', base=STOsTask)
def approve_map_2_level_task(*args, **kwargs):
    approve_map_2_level()


@shared_task(name='[Change Address] resolved_ticket_incorrect_format_task', base=STOsTask)
def resolved_ticket_incorrect_format_task(*args, **kwargs):
    resolved_ticket_incorrect_format()


@shared_task(name='[SLA Tool] get_need_call_tasks', base=STOsTask)
def collect_all_data_task():
    return chain(
        collect_ticket_change_address_task.s(),
        manual_ticket_have_alo_link_task.s(),
        load_order_info_task.s(),
        resolved_rts_and_last_status_task.s(),
        resolved_ticket_system_create_task.s(),
        resolved_ticket_storage_max_stored_task.s(),
        resolved_have_changed_address_task.s(),
        resolved_ticket_tokgistics_task.s(),
        approve_hcm_dn_hn_task.s(),
        resolved_ticket_incorrect_format_task.s(),
        approve_map_2_level_task.s(),
    )()
