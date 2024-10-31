from django.db import models

from core.base.model import BaseModel


class Zone(BaseModel):
    id = models.IntegerField(primary_key=True)
    legacy_zone_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    hub_id = models.IntegerField(null=True, blank=True)
    short_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'Zone'
        verbose_name_plural = 'Zones'

    def __str__(self):
        return self.name


class Hub(BaseModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    region = models.CharField(max_length=255, null=True, blank=True)
    area = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=True)
    short_name = models.CharField(max_length=255, null=True, blank=True)
    sort_hub = models.BooleanField(default=False)
    facility_type = models.CharField(max_length=255, null=True, blank=True)
    opv2_created_at = models.DateTimeField(auto_now_add=True)
    opv2_updated_at = models.DateTimeField(auto_now=True)
    virtual_hub = models.BooleanField(default=False)
    parent_hub = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Hub'
        verbose_name_plural = 'Hubs'

    def __str__(self):
        return self.name
