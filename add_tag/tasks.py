from celery import shared_task

from core.base.task import STOsQueueOnce
from .handler.b2b_prior.collect_data import collect_data_from_redash
from .handler.b2b_prior.core import add_tag


@shared_task(name='[Add Tag] B2B Prior', base=STOsQueueOnce, once={'graceful': True})
def add_prior_tag_for_b2b():
    collect_data_from_redash()
    add_tag()
