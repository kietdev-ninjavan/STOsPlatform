import time

from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.auto_cancel_missing.collect_data import collect_ticket_missing
from .handler.auto_cancel_missing.resolve import resolve_missing, check_need_resolve
from .handler.change_address.alo_link import solve_ticket_have_alo_link
from .handler.change_address.approve import (
    approve_hcm_dn_hn,
    approve_map_2_level
)
from .handler.change_address.collect_data import (
    collect_ticket_change_address,
    load_ticket_change_address_order_info
)
from .handler.change_address.detect import detect_address
from .handler.change_address.manual import (
    skip_ticket_manual_resolve
)
from .handler.change_address.output import out_to_gsheet_change_address
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


@shared_task(name='[Reco Ticket] Handle Ticket Change Address', base=STOsQueueOnce, once={'graceful': True})
def handle_change_address_task():
    collect_ticket_change_address()
    load_ticket_change_address_order_info()
    skip_ticket_manual_resolve()
    solve_ticket_have_alo_link()
    resolved_rts_and_last_status()
    resolved_ticket_system_create()
    resolved_ticket_storage_max_stored()
    resolved_have_changed_address()
    resolved_ticket_tokgistics()
    detect_address()
    time.sleep(5)
    detect_address()
    approve_hcm_dn_hn()
    approve_map_2_level()
    resolved_ticket_incorrect_format()
    out_to_gsheet_change_address()


@shared_task(name='[Reco Ticket] Handle Ticket Change Date', base=STOsQueueOnce, once={'graceful': True})
def handle_change_date_task():
    collect_ticket_change_date()
    load_order_info_change_date()
    have_rts_or_last_status()
    not_have_first_delivery_date()
    detect_date()
    time.sleep(5)
    detect_date()
    more_than_five_date()
    approve_tickets()
    incorrect_format_date()


@shared_task(name='[Reco Ticket] Handle Ticket Change Date Apply Action', base=STOsQueueOnce, once={'graceful': True})
def handle_change_date_apply_action_task():
    apply_action()


@shared_task(name='[Reco Ticket] Handle Auto Cancel Missing', base=STOsQueueOnce, once={'graceful': True})
def handle_auto_cancel_missing_task():
    collect_ticket_missing()
    check_need_resolve()
    resolve_missing()
