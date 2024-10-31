from django.db import models

from opv2.base.route import BaseRoute, BaseDriver


class Driver(BaseDriver):
    shipper_group = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'


class Route(BaseRoute):
    shipper_group = models.CharField(max_length=255, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='routes', null=True, blank=True)

    class Meta:
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
