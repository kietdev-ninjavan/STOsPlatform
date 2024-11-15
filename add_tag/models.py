from django.db import models

from core.base.model import BaseModel


class PriorB2B(BaseModel):
    order_id = models.BigIntegerField()
    tracking_id = models.CharField(max_length=255)
    granular_status = models.CharField(max_length=255)
    shipper_id = models.BigIntegerField()
    shipper_name = models.CharField(max_length=255)
    curr_zone_name = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField()
    pickup_datetime = models.DateTimeField()
    pickup_hub_name = models.CharField(max_length=255)
    delivery_hub_name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    date_to_prior = models.DateField()

    class Meta:
        verbose_name = 'Prior Tag B2B'
        verbose_name_plural = 'Prior Tag B2B'

