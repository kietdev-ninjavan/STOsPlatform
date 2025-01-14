from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.bulk_reship import wms_bulk_reship
from .handler.collect_data import (
    warehouse_holding,
    update_opv2_info,
    update_wms_info
)
from .handler.dispose import wms_dispose
from .handler.putaway import wms_putaway
from .handler.relabel import wms_relabel


@shared_task(name='WMS Collect Data', base=STOsQueueOnce, once={'graceful': True})
def collect_data():
    update_opv2_info()
    update_wms_info()


@shared_task(name="WMS Pre Processing", base=STOsQueueOnce, once={'graceful': True})
def pre_process():
    warehouse_holding()
    wms_putaway()
    collect_data.apply_async()


@shared_task(name="WMS Bulk Reship", base=STOsQueueOnce, once={'graceful': True})
def reship():
    wms_bulk_reship()
    collect_data.apply_async()


@shared_task(name="WMS Dispose", base=STOsQueueOnce, once={'graceful': True})
def dispose():
    wms_dispose()
    collect_data.apply_async()


@shared_task(name="WMS Relabel", base=STOsQueueOnce, once={'graceful': True})
def relabel():
    wms_relabel()
    collect_data.apply_async()
