from django.db import models

from opv2.base.order import BaseOrder


class Order(BaseOrder):
    changed_address_at = models.DateTimeField(null=True, blank=True)
    added_tag_at = models.DateTimeField(null=True, blank=True)
    cs_created_at = models.DateTimeField(null=True, blank=True)
