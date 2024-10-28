from django.db import models

from core.base.model import BaseModel


class BaseDriver(BaseModel):
    class Meta:
        abstract = True

    driver_id = models.AutoField(primary_key=True)
    driver_name = models.CharField(max_length=255, null=False)
    enabled = models.BooleanField(null=False, default=True)
    free = models.BooleanField(null=False, default=True)


class BaseRoute(BaseModel):
    class Meta:
        abstract = True

    route_id = models.AutoField(primary_key=True)
    archived = models.BooleanField(null=False, default=False)
