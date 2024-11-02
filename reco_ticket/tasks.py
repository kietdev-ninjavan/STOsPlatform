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
from .handler.change_address.detect import detect_address
from .handler.change_address.manual import manual_ticket_have_alo_link
from .handler.change_address.output import out_to_gsheet as change_address_out_to_gsheet
from .handler.change_address.resolve import (
    resolved_rts_and_last_status,
    resolved_ticket_system_create,
    resolved_ticket_storage_max_stored,
    resolved_have_changed_address,
    resolved_ticket_tokgistics,
    resolved_ticket_incorrect_format
)
from .handler.change_date.actions import (
    not_have_first_delivery_date,
    have_rts_or_last_status,
    more_than_five_date,
    incorrect_format_date,
    approve_tickets,
    apply_action
)
from .handler.change_date.collect_data import (
    collect_ticket_change_date,
    load_order_info_change_date
)
from .handler.change_date.detect import detect_date


# region Change Address
@shared_task(name='[Change Address] collect_ticket_change_address_task', base=STOsTask, once={'graceful': True})
def collect_ticket_change_address_task(*args, **kwargs):
    collect_ticket_change_address()


@shared_task(name='[Change Address] manual_ticket_have_alo_link_task', base=STOsTask, once={'graceful': True})
def manual_ticket_have_alo_link_task(*args, **kwargs):
    manual_ticket_have_alo_link()


@shared_task(name='[Change Address] load_order_info_task', base=STOsTask, once={'graceful': True})
def load_order_info_task(*args, **kwargs):
    load_order_info()


@shared_task(name='[Change Address] resolved_rts_and_last_status_task', base=STOsTask, once={'graceful': True})
def resolved_rts_and_last_status_task(*args, **kwargs):
    resolved_rts_and_last_status()


@shared_task(name='[Change Address] resolved_ticket_system_create_task', base=STOsTask, once={'graceful': True})
def resolved_ticket_system_create_task(*args, **kwargs):
    resolved_ticket_system_create()


@shared_task(name='[Change Address] resolved_ticket_storage_max_stored_task', base=STOsTask, once={'graceful': True})
def resolved_ticket_storage_max_stored_task(*args, **kwargs):
    resolved_ticket_storage_max_stored()


@shared_task(name='[Change Address] resolved_have_changed_address_task', base=STOsTask, once={'graceful': True})
def resolved_have_changed_address_task(*args, **kwargs):
    resolved_have_changed_address()


@shared_task(name='[Change Address] resolved_ticket_tokgistics_task', base=STOsTask, once={'graceful': True})
def resolved_ticket_tokgistics_task(*args, **kwargs):
    resolved_ticket_tokgistics()


@shared_task(name='[Change Address] detect_address_task', base=STOsTask, once={'graceful': True})
def detect_address_task(*args, **kwargs):
    detect_address()


@shared_task(name='[Change Address] approve_hcm_dn_hn_task', base=STOsTask, once={'graceful': True})
def approve_hcm_dn_hn_task(*args, **kwargs):
    approve_hcm_dn_hn()


@shared_task(name='[Change Address] approve_map_2_level_task', base=STOsTask, once={'graceful': True})
def approve_map_2_level_task(*args, **kwargs):
    approve_map_2_level()


@shared_task(name='[Change Address] resolved_ticket_incorrect_format_task', base=STOsTask, once={'graceful': True})
def resolved_ticket_incorrect_format_task(*args, **kwargs):
    resolved_ticket_incorrect_format()


@shared_task(name='[Change Address] out_to_gsheet_task', base=STOsTask, once={'graceful': True})
def change_address_out_to_gsheet_task(*args, **kwargs):
    change_address_out_to_gsheet()


@shared_task(name='[Change Address] Handler Ticket Change Address', base=STOsTask, once={'graceful': True})
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
        detect_address_task.s(),
        detect_address_task.s(),
        approve_hcm_dn_hn_task.s(),
        resolved_ticket_incorrect_format_task.s(),
        approve_map_2_level_task.s(),
        change_address_out_to_gsheet_task.s(),
    )()


# endregion

# region Change Date
@shared_task(name='[Change Date] load_order_info_task', base=STOsTask, once={'graceful': True})
def collect_ticket_change_date_task(*args, **kwargs):
    collect_ticket_change_date()


@shared_task(name='[Change Date] load_order_info_task', base=STOsTask, once={'graceful': True})
def load_order_info_change_date_task(*args, **kwargs):
    load_order_info_change_date()


@shared_task(name='[Change Date] detect_date_task', base=STOsTask, once={'graceful': True})
def detect_date_task(*args, **kwargs):
    detect_date()


@shared_task(name='[Change Date] not_have_first_delivery_date_task', base=STOsTask, once={'graceful': True})
def not_have_first_delivery_date_task(*args, **kwargs):
    not_have_first_delivery_date()


@shared_task(name='[Change Date] have_rts_or_last_status_task', base=STOsTask, once={'graceful': True})
def have_rts_or_last_status_task(*args, **kwargs):
    have_rts_or_last_status()


@shared_task(name='[Change Date] more_than_five_date_task', base=STOsTask, once={'graceful': True})
def more_than_five_date_task(*args, **kwargs):
    more_than_five_date()


@shared_task(name='[Change Date] incorrect_format_date_task', base=STOsTask, once={'graceful': True})
def incorrect_format_date_task(*args, **kwargs):
    incorrect_format_date()


@shared_task(name='[Change Date] approve_tickets_task', base=STOsTask, once={'graceful': True})
def approve_tickets_task(*args, **kwargs):
    approve_tickets()


@shared_task(name='[Change Date] apply_action_task', base=STOsTask, once={'graceful': True})
def apply_action_task(*args, **kwargs):
    apply_action()


@shared_task(name='[Change Date] Handler Ticket Change Date', base=STOsTask, once={'graceful': True})
def ticket_change_date_task():
    return chain(
        collect_ticket_change_date_task.s(),
        load_order_info_change_date_task.s(),
        not_have_first_delivery_date_task.s(),
        have_rts_or_last_status_task.s(),
        detect_date_task.s(),
        detect_address_task.s(),
        more_than_five_date_task.s(),
        incorrect_format_date_task.s(),
        approve_tickets_task.s(),
    )()

# endregion
