from django.db import models

from core.base.model import BaseModel


class TicketStatusChoices(models.IntegerChoices):
    PENDING = 1, 'Pending'
    IN_PROGRESS = 2, 'In Progress'
    RESOLVED = 3, 'Resolved'
    PENDING_SHIPPER = 9, 'Pending Shipper'
    ON_HOLD = 8, 'On Hold'
    CANCELLED = 13, 'Cancelled'


class TicketTypeChoices(models.IntegerChoices):
    DAMAGED = 1, 'DM'
    MISSING = 2, 'MI'
    SELF_COLLECTION = 3, 'SC'
    PARCEL_EXCEPTION = 4, 'PE'
    SHIPPER_ISSUE = 5, 'SI'
    PARCEL_ON_HOLD = 6, 'PH'
    SLA_BREACH = 7, 'SB'


class TicketSubTypeChoices(models.IntegerChoices):
    INACCURATE_ADDRESS = 1, "IA"
    RESTRICTED_ZONES = 2, "RZ"
    COMPLETED_ORDER = 3, "CO"
    CANCELLED_ORDER = 4, "CN"
    CUSTOMER_REJECTED = 5, "CR"
    NO_ORDER = 6, "NO"
    OVERWEIGHT_OVERSIZED = 7, "OO"
    POOR_PACKAGING = 8, "PP"
    DUPLICATE_PARCEL = 9, "DP"
    REJECTED_RETURN = 10, "RR"
    MAXIMUM_ATTEMPTS_DELIVERY = 30, "MA"
    DISPUTED_ORDER_INFO = 34, "DO"
    CUSTOMER_REQUEST = 38, "CQ"
    SHIPPER_REQUEST = 42, "SQ"
    DP_OVERSIZED = 44, "DZ"
    WRONG_AV_RACK_HUB = 46, "WR"
    REQUEST_RECEIPT = 48, "RC"
    RESTRICTED_GOODS = 50, "RG"
    NO_LABEL = 52, "NL"
    PAYMENT_PENDING_NINJA_DIRECT = 53, "ND"
    MAXIMUM_ATTEMPTS_RTS = 54, "MR"
    POOR_LABELLING = 55, "PL"
    SUSPICIOUS_PARCEL = 56, "SP"
    ROBO_CALL = 57, "RO"
    ROBO_CHAT = 58, "RH"
    DETAINED_PARCEL = 59, "DE"


class TicketOutcome(models.TextChoices):
    RESUME_DELIVERY = 'RESUME DELIVERY', 'Resume Delivery'
    RTS = 'RTS', 'Return to Sender'


class BaseTicket(BaseModel):
    ticket_id = models.BigIntegerField(primary_key=True)
    tracking_id = models.CharField(max_length=255, null=False)
    ticket_status = models.IntegerField(choices=TicketStatusChoices.choices, null=True, blank=True)
    ticket_type = models.IntegerField(choices=TicketTypeChoices.choices, null=True, blank=True)
    ticket_sub_type = models.IntegerField(choices=TicketSubTypeChoices.choices, null=True, blank=True)
    hub_id = models.BigIntegerField(null=True, blank=True)
    investigating_hub_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        abstract = True
