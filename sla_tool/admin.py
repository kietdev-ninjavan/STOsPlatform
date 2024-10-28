from core.base.admin import BaseAdmin
from stos.admin import stos_platform_admin
from .models import BreachSLACall, ExtendSLATracking, ShopeeBacklog


class BreachSLACallAdmin(BaseAdmin):
    list_display = (
        'tracking_id',
        'granular_status',
        'order_id',
        'rts',
        'shipper_group',
        'shipper_name',
        'num_of_attempts',
        'to_name',
        'to_contact',
        'to_address1',
        'cod',
        'item_description',
        'hub_id',
        'hub_name',
        'hub_region',
        'last_fail_attempt',
        'gform_url',
        'updated_at',
        'call_type',
    )
    search_fields = (
        'tracking_id',
        'granular_status',
        'order_id',
        'rts',
        'shipper_group',
        'shipper_name',
        'num_of_attempts',
        'to_name',
        'to_contact',
        'to_address1',
        'cod',
        'item_description',
        'hub_id',
        'hub_name',
        'hub_region',
        'last_fail_attempt',
        'gform_url',
        'updated_at',
        'call_type',
    )


stos_platform_admin.register(BreachSLACall, BreachSLACallAdmin)


class ExtendSLATrackingAdmin(BaseAdmin):
    list_display = (
        'tracking_id',
    )
    search_fields = (
        'tracking_id',
    )


stos_platform_admin.register(ExtendSLATracking, ExtendSLATrackingAdmin)


class ShoppeBacklogAdmin(BaseAdmin):
    list_display = (
        'tracking_id',
        'backlog_type',
        'order_sn',
        'consignment_no',
        'return_sn',
        'return_id',
        'aging_from_lost_threshold',
        'create_time',
        'pickup_done_time',
    )
    search_fields = (
        'tracking_id',
        'backlog_type',
        'order_sn',
        'consignment_no',
        'return_sn',
        'return_id',
        'aging_from_lost_threshold',
        'create_time',
        'pickup_done_time',
    )


stos_platform_admin.register(ShopeeBacklog, ShoppeBacklogAdmin)
