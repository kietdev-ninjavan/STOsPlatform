from django.db import models

from core.base.model import BaseModel
from opv2.base.pickup import BasePickup
from opv2.base.route import BaseRoute


class Route(BaseRoute):
    driver_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = 'Fail Pickup Route'
        verbose_name_plural = 'Fail Pickup Routes'


class PickupJob(BasePickup):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='pickup_jobs', null=True, blank=True)
    driver_id = models.IntegerField(null=True)
    pickup_schedule_date = models.DateField(null=True)
    shipper_address = models.CharField(max_length=255, null=True)
    call_center_status = models.CharField(max_length=255, null=True)
    call_center_sent_time = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'Fail Pickup Job'
        verbose_name_plural = 'Fail Pickup Jobs'


class PickupJobOrder(BaseModel):
    """
    Model to store job packet information.
    """
    order_id = models.IntegerField()
    job_id = models.ForeignKey(PickupJob, on_delete=models.CASCADE, related_name='packets')
    tracking_id = models.CharField(max_length=255, null=True)
    parcel_size = models.CharField(max_length=255, null=True)

    class Meta:
        verbose_name = 'Fail Pickup Job Order'
        verbose_name_plural = 'Fail Pickup Job Orders'
