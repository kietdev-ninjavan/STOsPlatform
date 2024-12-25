from django.db import models
from core.base.model import BaseModel


class OrigOrders(BaseModel):
    date_input = models.CharField(max_length=255, blank = True)
    tracking_id = models.CharField(max_length=255, blank = True)
    granular_status = models.CharField(max_length=255, blank = True)
    wms_status = models.CharField(max_length=255, blank = True)
    bin_name = models.CharField(max_length=255, blank = True)
    putaway_datetime = models.CharField(max_length=255, blank = True)
    picklist_uploaded_timestamp = models.CharField(max_length=255, blank = True)
    pending_pick_timestamp = models.CharField(max_length=255, blank = True)
    pick_timestamp = models.CharField(max_length=255, blank = True)
    pack_timestamp = models.CharField(max_length=255, blank = True)
    auto_dispose = models.SmallIntegerField(null=True, default=0)

    class Meta:
        verbose_name = 'WMS Orig Order'
        verbose_name_plural = 'WMS Orig Orders'
        
class ReshipOrders(BaseModel):
    date_input = models.CharField(max_length=255, blank = True)
    tracking_id = models.CharField(max_length=255, blank = True)
    source = models.CharField(max_length=255, blank = True, default = 'normal')
    weight = models.FloatField(null=True, blank=True)
    bag_name = models.CharField(max_length=255, blank = True)
    bag_id = models.BigIntegerField(null=True, blank=True)
    session_id = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'WMS Reship Order'
        verbose_name_plural = 'WMS Reship Orders'  
        
class DisposeOrders(BaseModel):
    date_input = models.CharField(max_length=255, blank = True)
    tracking_id = models.CharField(max_length=255, blank = True)
    source = models.CharField(max_length=255, blank = True, default = 'normal')
    bag_name = models.CharField(max_length=255, blank = True)
    bag_id = models.BigIntegerField(null=True, blank=True)
    session_id = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'WMS Dispose Order'
        verbose_name_plural = 'WMS Dispose Orders'

class RelabelOrders(BaseModel):
    date_input = models.CharField(max_length=255, blank = True)
    tracking_id = models.CharField(max_length=255, blank = True)
    relabel_tracking_id = models.CharField(max_length=255, blank = True)
    source = models.CharField(max_length=255, blank = True, default = 'normal')
    
    class Meta:
        verbose_name = 'WMS Relabel Order'
        verbose_name_plural = 'WMS Relabel Orders'