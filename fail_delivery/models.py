from django.db import models
from core.base.model import BaseModel
from opv2.base.route import BaseRoute, BaseDriver


class ReasonGroup(models.TextChoices):
    delay = "Khách hẹn ngày/giờ giao hàng"
    refused = "Khách hủy đơn hàng"
    cannot_contact = "Không liên lạc được khách"
    unknown = "Unknown"
    
class Driver(BaseDriver):
    class Meta:
        verbose_name = 'Fail Delivery Attempt'
        verbose_name_plural = 'Fail Delivery Attempts'

    def __str__(self):
        return self.driver_name


class Route(BaseRoute):
    reason_group = models.CharField(
        max_length=255,
        choices=ReasonGroup.choices,
        null=True,
        blank=True
    )
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='routes', null=True, blank=True)

    class Meta:
        verbose_name = 'Fail Delivery Attempt'
        verbose_name_plural = 'Fail Delivery Attempts'

    
    
class Source(BaseModel) :
    tracking_id = models.CharField(max_length=255, blank = True)
    shipper_name = models.CharField(max_length=255, blank = True)
    response_type = models.CharField(max_length=255, blank = True)
    customer_response = models.CharField(max_length=255, blank = True)
    
    class Meta:
        verbose_name = 'Fail Delivery Source'
        verbose_name_plural = 'Fail Delivery Sources'
        
        
class FailOrders(BaseModel) :
    tracking_id = models.CharField(max_length=255, blank = True)
    order_id = models.BigIntegerField(null=True, blank=True)
    granular_status = models.CharField(max_length=255, blank = True)
    rts = models.SmallIntegerField(null=True, default=0)
    total_attempts = models.BigIntegerField(null=True, blank=True)
    refused_attempts = models.BigIntegerField(null=True, blank=True)
    shipper_name = models.CharField(max_length=255, blank = True)
    source_type = models.CharField(max_length=255, blank = True)
    customer_response = models.CharField(max_length=255, blank = True)
    prts_flag = models.SmallIntegerField(null=True, default=0)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='fail_orders', null=True, blank=True)
    reason_group = models.CharField(
        max_length=255,
        choices=ReasonGroup.choices,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Fail Delivery Order'
        verbose_name_plural = 'Fail Delivery Orders'
        
class TagConfirm(BaseModel) :
    tracking_id = models.CharField(max_length=255, blank = True)
    order_id = models.BigIntegerField(null=True, blank=True)
    granular_status = models.CharField(max_length=255, blank = True)
    rts = models.SmallIntegerField(null=True, default=0)
    shipper_name = models.CharField(max_length=255, blank = True)
    source_type = models.CharField(max_length=255, blank = True)
    customer_response = models.CharField(max_length=255, blank = True)
    
    class Meta:
        verbose_name = 'Fail Delivery - Tag Confirm'
        verbose_name_plural = 'Fail Delivery - Tag Confirm'