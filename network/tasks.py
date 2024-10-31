from celery import shared_task

from core.base.task import STOsTask
from .handlers.hub import collect_hubs
from .handlers.zone import collect_zones


@shared_task(base=STOsTask, name='[Background] Collect Zones')
def collect_zones_task():
    collect_zones()


@shared_task(base=STOsTask, name='[Background] Collect Hubs')
def collect_hubs_task():
    collect_hubs()
