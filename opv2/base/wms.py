from django.db import models

from core.base.model import BaseModel
from enum import Enum

class WMSOrderStatus(models.TextChoices): 
   asn_uploaded = "ASN_UPLOADED"
   in_warehouse = "IN_WAREHOUSE"
   pick_requested = "PICK_REQUESTED"
   pending_pick = "PENDING_PICK"
   pick_reship = "PICKED_BULK_RESHIP"
   pick_dispose = "PICKED_DISPOSE"
   pick_relabel = "PICKED_RELABEL"
   pack_reship = "PACKED_BULK_RESHIP"
   pack_dispose = "PACKED_DISPOSE"
   pack_relabel = "PACKED_RELABEL"
   handover_reship = "HANDOVER_TO_BULK_RESHIP"
   
class WMSBin(models.IntegerChoices):
    bin_1 = 6805
    bin_2 = 6806
    bin_3 = 6807
    bin_4 = 6808
    bin_5 = 6809
    
class WMSAction(Enum):    
    dispose = ("DISPOSE","/parcels/packdispose")
    reship = ("BULK_RESHIP","/parcels/packreship")
    relabel = ("RELABEL","/parcels/packrelabel")
    
    def __init__(self, action, path):
        self.action = action
        self.path = path
    
class BaseWms(BaseModel):
    parcel_id = models.BigIntegerField(primary_key=True) 
    tracking_id = models.CharField(max_length=255)
    order_status = models.CharField(choices=WMSOrderStatus.choices, null=True)
    bin_id = models.IntegerField(choices=WMSBin.choices, null=True)
    putaway_timestamp = models.CharField(max_length=255, null=True)
    picklist_upload_timestamp = models.CharField(max_length=255, null=True)
    pending_pick_timestamp = models.CharField(max_length=255, null=True)
    pick_timestamp = models.CharField(max_length=255, null=True)
    pack_timestamp = models.CharField(max_length=255, null=True)
    auto_dispose = models.SmallIntegerField(default =0)
    
    class Meta:
        abstract = True