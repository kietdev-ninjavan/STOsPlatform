from django.db import models

from core.base.model import BaseModel


# Order Status
class StatusChoices(models.TextChoices):
    completed = "Completed", "Completed"
    cancelled = "Cancelled", "Cancelled"


# Order Granular Status
class GranularStatusChoices(models.TextChoices):
    en_route = "En-route to Sorting Hub", "En-route to Sorting Hub"
    arrived_sorting = "Arrived at Sorting Hub", "Arrived at Sorting Hub"
    pending_reschedule = "Pending Reschedule", "Pending Reschedule"
    pending_pickup = "Pending Pickup", "Pending Pickup"
    pending_pickup_at_dp = "Pending Pickup at Distribution Point", "Pending Pickup at Distribution Point"
    on_vehicle = "On Vehicle for Delivery", "On Vehicle for Delivery"
    on_hold = "On Hold", "On Hold"
    t3pl = "Transferred to 3PL", "Transferred to 3PL"
    # Last status
    completed = "Completed", "Completed"
    cancelled = "Cancelled", "Cancelled"
    rts = "Returned to Sender", "Returned to Sender"


# Base Order Model
class BaseOrder(BaseModel):
    class Meta:
        abstract = True

    tracking_id = models.CharField(max_length=255)
    order_id = models.BigIntegerField(null=True)
    status = models.CharField(max_length=255, choices=StatusChoices.choices, null=True)
    granular_status = models.CharField(max_length=255, choices=GranularStatusChoices.choices, null=True)
    rts = models.BooleanField(default=False)

    def __str__(self):
        return self.tracking_id
