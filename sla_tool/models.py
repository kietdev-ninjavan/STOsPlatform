from django.db import models

from core.base.model import BaseModel
from opv2.base.order import BaseOrder


class BreachSLACall(BaseOrder):
    shipper_group = models.CharField(max_length=255, null=True, blank=True)
    shipper_name = models.CharField(max_length=255, null=True, blank=True)
    num_of_attempts = models.IntegerField(default=False, null=False)
    to_name = models.CharField(max_length=255, null=True, blank=True)
    to_contact = models.CharField(max_length=255, null=True, blank=True)
    to_address1 = models.TextField(null=True, blank=True)
    cod = models.FloatField(null=True, blank=True)
    item_description = models.TextField(null=True, blank=True)
    hub_id = models.IntegerField(null=True, blank=True)
    hub_name = models.CharField(max_length=255, null=True, blank=True)
    hub_region = models.CharField(max_length=255, null=True, blank=True)
    last_fail_attempt = models.CharField(max_length=255, null=True, blank=True)
    gform_url = models.URLField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    call_type = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Breach SLA Call'
        verbose_name_plural = 'Breach SLA Calls'
        constraints = [
            models.UniqueConstraint(fields=['tracking_id', 'updated_at'], name='unique_breach_tracking_update')
        ]

    def __str__(self):
        return f"{self.tracking_id}"


class RecordSLACall(BaseModel):
    tracking_id = models.CharField(max_length=255, primary_key=True)
    collect_date = models.DateField(null=True, blank=True)


class ExtendSLATracking(BaseModel):
    tracking_id = models.CharField(primary_key=True, max_length=255)
    extend_days = models.IntegerField(null=True, blank=True)
    sla_date = models.DateField(null=True, blank=True)
    breach_sla_date = models.DateField(null=True, blank=True)
    first_sla_expectation = models.DateField(null=True, blank=True)
    breach_sla_expectation = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Extend SLA Tracking ID'
        verbose_name_plural = 'Extend SLA Tracking IDs'

    def __str__(self):
        return f"{self.tracking_id}"


class TiktokBacklog(BaseOrder):
    ticket_no = models.BigIntegerField(null=True, blank=True)
    tracking_id = models.CharField(max_length=255, primary_key=True)
    date = models.DateField(null=True, blank=True)
    backlog_type = models.CharField(max_length=255, null=True, blank=True)
    shipper_date = models.DateField(null=True, blank=True)
    extend_days = models.IntegerField(null=True, blank=True, default=2)
    extended_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tiktok Backlog'
        verbose_name_plural = 'Tiktok Backlogs'


class ShopeeBacklog(BaseOrder):
    tracking_id = models.CharField(max_length=255)
    backlog_type = models.CharField(max_length=255, null=True, blank=True)
    order_sn = models.CharField(max_length=255)
    return_sn = models.CharField(max_length=255, null=True, blank=True)
    return_id = models.BigIntegerField(null=True, blank=True)
    consignment_no = models.CharField(max_length=255, null=True, blank=True)
    aging_from_lost_threshold = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(null=True, blank=True)
    pickup_done_time = models.DateTimeField(null=True, blank=True)
    shipper_date = models.DateField(null=True, blank=True)
    extend_days = models.IntegerField(null=True, blank=True)
    extended_date = models.DateField(null=True, blank=True)
    zns_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Shopee Backlog'
        verbose_name_plural = 'Shopee Backlogs'
        constraints = [
            models.UniqueConstraint(fields=['tracking_id', 'order_sn'], name='unique_breach_tracking_order_sn')
        ]
