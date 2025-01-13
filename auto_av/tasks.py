from celery import shared_task

from core.base.task import STOsParallel
from .b2b.delivery.collect_data import collect_order_av_to_b2b_lm
from .b2b.delivery.b2b_lm import address_verification_to_b2b_lm
from .b2b.delivery.njv_lm import (
    update_order_info,
    update_parcel_size,
    address_verification_to_njv_lm
)


@shared_task(name='[Auto AV B2B LM] AV To B2B', base=STOsParallel)
def b2b_av_b2b_lm():
    collect_order_av_to_b2b_lm()
    address_verification_to_b2b_lm()


@shared_task(name='[Auto AV B2B LM] AV To B2B', base=STOsParallel)
def b2b_av_njv_lm():
    update_order_info()
    update_parcel_size()
    address_verification_to_njv_lm()
