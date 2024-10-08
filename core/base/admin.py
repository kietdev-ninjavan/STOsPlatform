from django.contrib import messages
from django.utils import timezone
from simple_history.admin import SimpleHistoryAdmin


class BaseAdmin(SimpleHistoryAdmin):
    """
    Base admin class to handle soft-delete functionality in Django admin.
    """

    def get_queryset(self, request):
        """
        Override the default queryset to only return active (non-deleted) objects.
        """
        return self.model.all_objects.filter(delete_at__isnull=True)

    def delete_model(self, request, obj):
        """
        Perform a soft delete when deleting an object from the admin.
        """
        obj.delete()

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

    actions = ['delete_queryset', 'restore_selected']
