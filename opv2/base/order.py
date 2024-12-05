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


class TagChoices(models.IntegerChoices):
    EXCL_FMAJ = 74, 'Excl Fmaj'
    GTC = 30, 'GTC'
    UUTIEN32 = 45, 'UUTIEN32'
    OVERCAP = 104, 'Overcap'
    OPEX = 121, 'Opex'
    PRIOR = 63, 'Prior'
    CONFIRMED = 126, 'Confirmed'
    FP = 127, 'FP'
    FP2 = 128, 'FP2'
    FP3 = 129, 'FP3'
    FP4 = 130, 'FP4'
    FP5 = 135, 'FP5'
    SANG = 139, 'Sang'
    CHIEU = 140, 'Chieu'
    AIR = 65, 'Air'
    RTS_FHS = 16, 'RTS-FHS'
    RTS_VCB_01 = 151, 'RTS-VCB-01'
    RTS_VCB_02 = 152, 'RTS-VCB-02'
    RTS_VCB_03 = 153, 'RTS-VCB-03'
    RTS_VCB_04 = 154, 'RTS-VCB-04'
    RTS_VCB_05 = 155, 'RTS-VCB-05'
    RTS_VCB_06 = 156, 'RTS-VCB-06'
    RTS_VCB_07 = 157, 'RTS-VCB-07'
    RTS_VCB_08 = 158, 'RTS-VCB-08'
    RTS_VCB_09 = 159, 'RTS-VCB-09'
    RTS_VCB_10 = 160, 'RTS-VCB-10'
    RTS_VCB_11 = 161, 'RTS-VCB-11'
    RTS_VCB_12 = 162, 'RTS-VCB-12'
    RTS_VCB_13 = 163, 'RTS-VCB-13'
    RTS_VCB_14 = 164, 'RTS-VCB-14'
    RTS_VCB_15 = 165, 'RTS-VCB-15'
    RTS_VCB_16 = 166, 'RTS-VCB-16'
    RTS_VCB_17 = 167, 'RTS-VCB-17'
    RTS_VCB_18 = 168, 'RTS-VCB-18'
    RTS_VCB_19 = 169, 'RTS-VCB-19'
    RTS_VCB_20 = 170, 'RTS-VCB-20'
    RTS_SHEIN = 171, 'RTS - SHEIN'


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
