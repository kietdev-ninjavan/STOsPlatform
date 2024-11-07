from celery import shared_task

from core.base.task import STOsQueueOnce
from .handlers.hub import collect_hubs
from .handlers.zone import collect_zones


@shared_task(base=STOsQueueOnce, name='[Background] Collect Zones', once={'graceful': True})
def collect_zones_task():
    collect_zones()


@shared_task(base=STOsQueueOnce, name='[Background] Collect Hubs', once={'graceful': True})
def collect_hubs_task():
    collect_hubs()
