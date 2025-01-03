from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.collect_data import (
    collect_vendor_call_data,
    collect_vendor_call_proactive,
    load_order_info,
    load_ticket_info_sla,
    load_ticket_info_proactive
)
from .handler.order import (
    parcel_sweeper_live,
    routing_orders,
    reschedule_order
)
from .handler.proactive import cancel_ticket_proactive
from .handler.route import (
    fetch_route,
)
from .handler.sla import (
    pull_route_ovfd,
    cancel_ticket_missing,
    create_ms_ticket_again
)


@shared_task(name='[Pre Success] Fetch Status', base=STOsQueueOnce, once={'graceful': True})
def fetch_task():
    load_order_info()
    fetch_route()


@shared_task(name='[Pre Success] Handle without reschedule', base=STOsQueueOnce, once={'graceful': True})
def collect_vendor_call_data_with_task():
    collect_vendor_call_data()
    load_order_info()
    parcel_sweeper_live()
    routing_orders()
    fetch_task.apply_async()


@shared_task(name='[Pre Success] Handle with reschedule', base=STOsQueueOnce, once={'graceful': True})
def collect_vendor_call_data_task():
    collect_vendor_call_data()
    load_order_info()
    reschedule_order()
    parcel_sweeper_live()
    routing_orders()
    fetch_task.apply_async()


@shared_task(name='[Pre Success] Handler SLA', base=STOsQueueOnce, once={'graceful': True})
def sla_task():
    """Run all tasks for SLA at once 22:00"""
    collect_vendor_call_data()
    load_order_info()
    load_ticket_info_sla()
    cancel_ticket_missing()
    pull_route_ovfd()
    reschedule_order()
    parcel_sweeper_live(sla_enabled=True)
    routing_orders()
    fetch_task.apply_async()


@shared_task(name='[Pre Success] Create MS Ticket Again', base=STOsQueueOnce, once={'graceful': True})
def creat_ms_again_task():
    create_ms_ticket_again()


@shared_task(name='[Pre Success] Handle proactive', base=STOsQueueOnce, once={'graceful': True})
def handle_proactive():
    collect_vendor_call_proactive()
    load_order_info()
    reschedule_order()
    load_ticket_info_proactive()
    cancel_ticket_proactive()
    load_order_info()
    parcel_sweeper_live()
    routing_orders()
    fetch_task.apply_async()
