from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.action import create_cs_ticket, change_address, add_tag
from .handler.collect_data import collect_order_data


@shared_task(name='[Shein] Handle Find ZNS', base=STOsQueueOnce, once={'graceful': True})
def shein_task():
    collect_order_data()
    create_cs_ticket()
    change_address()
    add_tag()
