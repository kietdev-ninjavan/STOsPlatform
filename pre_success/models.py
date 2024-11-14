from django.db import models

from opv2.base.order import BaseOrder
from opv2.base.route import BaseRoute, BaseDriver


class ShipperGroup(models.TextChoices):
    tiktok = "TikTok Domestic"
    shopee = "Shopee"
    ttid = "TTDI"
    unknown = "Unknown"


class Driver(BaseDriver):
    class Meta:
        verbose_name = 'Pre Success Driver'
        verbose_name_plural = 'Pre Success Drivers'

    def __str__(self):
        return self.driver_name


class Route(BaseRoute):
    shipper_group = models.CharField(
        max_length=255,
        choices=ShipperGroup.choices,
        null=True,
        blank=True
    )
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='routes', null=True, blank=True)

    class Meta:
        verbose_name = 'Pre Success Route'
        verbose_name_plural = 'Pre Success Routes'


class Order(BaseOrder):
    waypoint_id = models.BigIntegerField(null=True, blank=True)
    time_stamp = models.CharField(max_length=255, null=True, blank=True)
    project_call = models.CharField(max_length=255, null=True, blank=True)
    ticket_id = models.BigIntegerField(null=True, blank=True)
    investigating_hub_id = models.IntegerField(null=True, blank=True)
    last_instruction = models.TextField(null=True, blank=True)
    dest_hub_id = models.IntegerField(null=True)
    parcel_sweeper = models.BooleanField(default=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    shipper_group = models.CharField(
        max_length=255,
        choices=ShipperGroup.choices,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Pre Success Order'
        verbose_name_plural = 'Pre Success Orders'
        constraints = [
            models.UniqueConstraint(fields=['tracking_id', 'project_call'], name='unique_tracking_project')
        ]
