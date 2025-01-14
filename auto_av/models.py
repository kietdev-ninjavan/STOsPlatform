from django.db import models

from opv2.base.order import BaseOrder


class StageChoices(models.TextChoices):
    B2B_AV = "B2B-AV", "B2B-AV"
    B2B_LM_AV = "B2B-LM-AV", "B2B-LM-AV"
    LM_AV = "LM-AV", "LM-AV"
    IN_QUEUE = "In Queue", "In Queue"
    NOT_VERIFIED = "Not Verified", "Not Verified"


class OrderB2B(BaseOrder):
    shipper_id = models.BigIntegerField(blank=True, null=True)
    waypoint = models.BigIntegerField()
    mps_id = models.BigIntegerField(blank=True, null=True)
    mps_sequence_number = models.IntegerField(blank=True, null=True)
    parcel_size = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    zone_id = models.IntegerField()
    hub_id = models.IntegerField()
    stage = models.CharField(max_length=255, choices=StageChoices.choices, default=StageChoices.NOT_VERIFIED)
