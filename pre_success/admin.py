from django import forms
from django.core.exceptions import ValidationError

from core.base.admin import BaseAdmin
from stos.admin import stos_platform_admin
from .models import Driver, Order, Route


# Route Admin Configuration
class RouteAdmin(BaseAdmin):
    list_display = ('route_id', 'archived', 'shipper_group', 'driver_name') + BaseAdmin.list_display
    list_filter = ['archived', 'shipper_group'] + BaseAdmin.list_filter
    search_fields = ('route_id',)

    # Custom method to display the driver's name in the RouteAdmin
    def driver_name(self, obj):
        return obj.driver.driver_name if obj.driver else 'No Driver Assigned'

    driver_name.admin_order_field = 'driver__driver_name'  # Allow sorting by driver_name


stos_platform_admin.register(Route, RouteAdmin)


# Order Admin Configuration
class OrderAdmin(BaseAdmin):
    list_display = ('tracking_id', 'granular_status', 'rts', 'project_call', 'route', 'shipper_group') + BaseAdmin.list_display
    list_filter = ['shipper_group', 'route', 'project_call'] + BaseAdmin.list_filter
    search_fields = ('tracking_id',)

    # Custom method to get the shipper group from the related Route
    def shipper_group(self, obj):
        return obj.route.shipper_group if obj.route else 'Unknown'

    shipper_group.admin_order_field = 'route__shipper_group'  # Allow sorting by shipper group


stos_platform_admin.register(Order, OrderAdmin)


# Driver Admin Configuration
class DriverForm(forms.ModelForm):
    # Allow driver_id to be set manually
    driver_id = forms.IntegerField(required=False)  # Allow id to be set manually

    class Meta:
        model = Driver
        fields = '__all__'

    def clean_driver_id(self):
        """Ensure the manually set driver_id doesn't conflict with the auto-increment behavior."""
        driver_id = self.cleaned_data.get('driver_id')
        if driver_id and Driver.objects.filter(driver_id=driver_id).exists():
            raise ValidationError(f"Driver ID {driver_id} is already in use.")
        return driver_id

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Assign the driver_id manually if provided
        driver_id = self.cleaned_data.get('driver_id')
        if driver_id:
            instance.driver_id = driver_id  # Manually set the driver_id if provided
        if commit:
            instance.save()
        return instance


class DriverAdmin(BaseAdmin):
    form = DriverForm
    list_display = ('driver_id', 'driver_name', 'enabled', 'free') + BaseAdmin.list_display
    search_fields = ('driver_name', 'driver_id')
    list_filter = ['enabled', 'free'] + BaseAdmin.list_filter

    def save_model(self, request, obj, form, change):
        # Handle saving logic, manually set driver_id if provided
        driver_id = form.cleaned_data.get('driver_id')
        if driver_id:
            obj.driver_id = driver_id  # Set driver_id if provided
        obj.save()


stos_platform_admin.register(Driver, DriverAdmin)
