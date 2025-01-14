from core.base.admin import BaseAdmin
from stos.admin import stos_platform_admin

from .models import Hub, HubB2B, Zone


class ZoneAdmin(BaseAdmin):
    list_display = ('legacy_zone_id', 'name', 'type', 'short_name', 'latitude', 'longitude') + BaseAdmin.list_display
    list_filter = ['type', 'hub_id'] + BaseAdmin.list_filter
    search_fields = ('name', 'short_name')


stos_platform_admin.register(Zone, ZoneAdmin)


class HubAdmin(BaseAdmin):
    list_display = ('name', 'country', 'city', 'latitude', 'longitude', 'region', 'area', 'active', 'short_name',
                    'sort_hub', 'facility_type', 'virtual_hub', 'parent_hub', 'b2b_hub') + BaseAdmin.list_display
    list_filter = ['country', 'region', 'area', 'active', 'sort_hub', 'facility_type', 'virtual_hub',
                   'parent_hub'] + BaseAdmin.list_filter
    search_fields = ('name', 'short_name')


stos_platform_admin.register(Hub, HubAdmin)


class HubB2BAdmin(BaseAdmin):
    list_display = ('hub_name', 'code', 'latitude', 'longitude') + BaseAdmin.list_display
    search_fields = ('hub_name', 'code')


stos_platform_admin.register(HubB2B, HubB2BAdmin)
