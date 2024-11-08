from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.collect_data import collect_job_data, collect_job_info, collect_packets
from .handler.fail_process import fail_job_sh, fail_job_kll
from .handler.report import report_fail_job
from .handler.routing import job_routing, start_route, archive_route


@shared_task(base=STOsQueueOnce, name='[Fail Pickup] Collect Job Data', once={'graceful': True})
def collect_job_data_task():
    collect_job_data()
    collect_job_info()


@shared_task(base=STOsQueueOnce, name='[Fail Pickup] Routing', once={'graceful': True})
def routing_and_collect_packets():
    job_routing()


@shared_task(base=STOsQueueOnce, name='[Fail Pickup] Start Fail KLL Job Task', once={'graceful': True})
def fail_all_job_task():
    collect_packets()
    start_route()
    fail_job_sh()
    fail_job_kll()


@shared_task(base=STOsQueueOnce, name='[Fail Pickup] Report Task', once={'graceful': True})
def report_task():
    report_fail_job()
    archive_route()
