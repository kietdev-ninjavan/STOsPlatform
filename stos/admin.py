from django.contrib import admin
from django.db.models import Prefetch
from django_celery_beat.admin import PeriodicTaskAdmin

from .models import ExtendedPeriodicTask, User


class STOsPlatformAdminSite(admin.AdminSite):
    site_header = "STOS Platform Admin"
    site_title = "STOS Platform Admin"
    index_title = "Welcome to STOS Platform Admin"


stos_platform_admin = STOsPlatformAdminSite(name='stos_platform_admin')


# region Tools Periodic Task
class TagsFilter(admin.SimpleListFilter):
    title = 'Tags'
    parameter_name = 'tags'

    def lookups(self, request, model_admin):
        # Optimized to only retrieve tags
        tags = ExtendedPeriodicTask.objects.exclude(tags__isnull=True).values_list('tags', flat=True)
        tags_set = {tag.strip() for tag_string in tags for tag in tag_string.split(',')}
        return [(tag, tag) for tag in tags_set]

    def queryset(self, request, queryset):
        # More explicit filtering
        if self.value():
            return queryset.filter(tags__icontains=self.value())
        return queryset


class CreatedByFilter(admin.SimpleListFilter):
    title = 'Created By'  # Display title in admin filter
    parameter_name = 'created_by'  # The query parameter for the filter

    def lookups(self, request, model_admin):
        # Prefetch periodic tasks to minimize DB hits
        creators = User.objects.prefetch_related(
            Prefetch('periodic_tasks', queryset=ExtendedPeriodicTask.objects.only('id'))
        ).distinct()

        return [(user.id, user.username) for user in creators]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected user from the filter
        if self.value():
            return queryset.filter(created_by_id=self.value())
        return queryset


class ExtendedPeriodicTaskAdmin(PeriodicTaskAdmin):
    list_display = PeriodicTaskAdmin.list_display + ('created_by', 'get_tags')
    list_filter = [CreatedByFilter, TagsFilter, 'enabled', 'one_off', 'created_date']
    search_fields = PeriodicTaskAdmin.search_fields + ('tags',)

    fieldsets = PeriodicTaskAdmin.fieldsets + (
        (None, {'fields': ('tags',)}),  # Add 'tags' to the form
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_tags(self, obj):
        tags = obj.get_tags()
        return ', '.join(tags) if tags else '-'

    get_tags.short_description = 'Tags'


stos_platform_admin.register(ExtendedPeriodicTask, ExtendedPeriodicTaskAdmin)
# endregion
