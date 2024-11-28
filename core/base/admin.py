from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin


class SoftDeleteFilter(SimpleListFilter):
    """
    Custom filter to allow admin users to filter between active and soft-deleted objects.
    """
    title = _('soft delete status')
    parameter_name = 'deleted'

    def lookups(self, request, model_admin):
        return (
            ('deleted', _('Deleted')),
            ('active', _('Active')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'deleted':
            return queryset.filter(delete_at__isnull=False)
        elif value == 'active':
            return queryset.filter(delete_at__isnull=True)
        return queryset.none() if value else queryset


class BaseAdmin(SimpleHistoryAdmin):
    """
    Base admin class to handle soft-delete functionality in Django admin.
    """
    list_display = ('is_deleted', 'delete_at')  # Display soft delete status
    list_filter = [SoftDeleteFilter, ]  # Add filter for active/soft deleted items
    actions = ('delete_queryset', 'restore_selected')

    exclude = ('delete_at',)  # Exclude delete_at field from the admin form

    def get_queryset(self, request):
        """
        Override the default queryset to show all objects including soft-deleted ones.
        """
        try:
            return self.model.all_objects.all()  # Require a custom manager for soft delete
        except AttributeError:
            return super().get_queryset(request)  # Fallback to default queryset

    def is_deleted(self, obj):
        """
        Display soft delete status in the list.
        """
        return obj.delete_at is not None

    is_deleted.boolean = True
    is_deleted.short_description = 'Soft Deleted'

    def delete_model(self, request, obj):
        """
        Perform a soft delete when deleting an object from the admin.
        """
        obj.delete()
        self.message_user(request, f"{obj} has been soft deleted.", messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        """
        Override the default bulk delete action to perform a soft delete.
        """
        queryset.update(delete_at=timezone.now())
        self.message_user(request, "Selected objects have been soft deleted.", messages.SUCCESS)

    def restore_selected(self, request, queryset):
        """
        Custom action to restore soft-deleted objects.
        """
        queryset.update(delete_at=None)
        self.message_user(request, "Selected objects have been restored.", messages.SUCCESS)

    restore_selected.short_description = "Restore selected soft-deleted items"

    def get_actions(self, request):
        """
        Disable delete action and use custom soft delete instead.
        """
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
