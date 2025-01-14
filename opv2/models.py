from django.db import models

from core.base.model import BaseModel


class ShipperB2B(BaseModel):
    shipper_id = models.BigIntegerField(primary_key=True)
    shipper_name = models.CharField(max_length=255)
