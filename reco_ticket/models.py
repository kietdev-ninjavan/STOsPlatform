from django.db import models

from core.base.model import BaseModel
from opv2.base.order import GranularStatusChoices
from opv2.base.ticket import BaseTicket


class SelfCollectionChoices(models.TextChoices):
    TT_DESTROYED_GOODS = 'TT_DESTROYED_GOODS', 'Tiktok Destroyed Goods'
    SP_DESTROYED_GOODS = 'SP_DESTROYED_GOODS', 'Shopee Destroyed Goods'


class TicketChangeDate(BaseTicket):
    created_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    exception_reason = models.TextField(null=True, blank=True)
    first_delivery_date = models.DateTimeField(null=True, blank=True)
    detected_date = models.DateField(null=True, blank=True)
    action = models.CharField(max_length=255, null=True, blank=True)
    action_reason = models.CharField(max_length=255, null=True, blank=True)
    apply_action = models.DateTimeField(null=True, blank=True)
    rts_flag = models.BooleanField(default=False)
    order_id = models.BigIntegerField(null=True, blank=True)
    order_status = models.CharField(
        max_length=255,
        choices=GranularStatusChoices.choices,
        null=True, blank=True
    )

    class Meta:
        verbose_name = 'Ticket Change Date'
        verbose_name_plural = 'Ticket Change Dates'


class TicketChangeAddress(BaseTicket):
    created_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    order_id = models.BigIntegerField(null=True, blank=True)
    exception_reason = models.TextField(null=True, blank=True)
    first_attempt_date = models.DateTimeField(null=True, blank=True)
    times_change = models.IntegerField(default=0)
    shipper_id = models.BigIntegerField(null=True, blank=True)
    province = models.CharField(max_length=255, null=True, blank=True)
    rts_flag = models.BooleanField(default=False)
    old_address = models.TextField(null=True, blank=True)
    old_province = models.CharField(max_length=255, null=True, blank=True)
    old_district = models.CharField(max_length=255, null=True, blank=True)
    old_ward = models.CharField(max_length=255, null=True, blank=True)
    zone_name = models.CharField(max_length=255, null=True, blank=True)
    order_status = models.CharField(
        max_length=255,
        choices=GranularStatusChoices.choices,
        null=True, blank=True
    )
    action = models.CharField(max_length=255, null=True, blank=True)
    action_reason = models.CharField(max_length=255, null=True, blank=True)
    out_sheet = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Ticket Change Address'
        verbose_name_plural = 'Ticket Change Addresses'


class DetectChangeAddress(BaseModel):
    input = models.TextField(null=True)
    address = models.TextField(null=True)
    province = models.CharField(max_length=255, null=True)
    district = models.CharField(max_length=255, null=True)
    ward = models.CharField(max_length=255, null=True)
    ticket = models.OneToOneField(TicketChangeAddress, on_delete=models.CASCADE, related_name='detect')

    class Meta:
        verbose_name = 'Detect Change Address'
        verbose_name_plural = 'Detect Change Addresses'


class TicketMissing(BaseTicket):
    order_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    shipper_id = models.BigIntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    ws_last_scan = models.DateTimeField(null=True, blank=True)
    ib_last_scan = models.DateTimeField(null=True, blank=True)
    sm_last_scan = models.DateTimeField(null=True, blank=True)
    need_resolve = models.BooleanField(default=False)
    resolve_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ticket Missing'
        verbose_name_plural = 'Tickets Missing'


class TicketSelfCollection(BaseTicket):
    type = models.CharField(
        max_length=255,
        choices=SelfCollectionChoices.choices,
        null=True, blank=True
    )
    resolve_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ticket Self Collection'
        verbose_name_plural = 'Tickets Self Collection'
