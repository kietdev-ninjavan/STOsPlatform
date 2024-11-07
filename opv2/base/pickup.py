from django.db import models

from core.base.model import BaseModel


class PickupJobStatusChoices(models.TextChoices):
    READY_FOR_ROUTING = "ready-for-routing", "Ready for Routing"
    ROUTED = "routed", "Routed"
    IN_PROGRESS = "in-progress", "In Progress"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    NO_POP = "no-pop", "No POP"


class BasePickup(BaseModel):
    job_id = models.IntegerField(primary_key=True)
    shipper_id = models.BigIntegerField(null=True)
    shipper_name = models.CharField(max_length=255, null=True)
    contact = models.CharField(max_length=20, null=True)
    waypoint_id = models.BigIntegerField(null=True)
    status = models.CharField(
        max_length=20,
        choices=PickupJobStatusChoices.choices,
        null=True
    )

    class Meta:
        abstract = True
