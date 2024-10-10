from django.contrib import admin
from django.db.models import Prefetch
from django_celery_beat.admin import (
    PeriodicTaskAdmin, IntervalScheduleAdmin, CrontabScheduleAdmin,
    SolarScheduleAdmin, ClockedScheduleAdmin
)
from django_celery_beat.models import (
    IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule
)

from core.base.admin import BaseAdmin
from .models import ExtendedPeriodicTask, User, Holiday, Config


class STOsPlatformAdminSite(admin.AdminSite):
    """Custom admin site for the STOS platform."""
    site_header = "STOS Platform Admin"
    site_title = "STOS Platform Admin"
    index_title = "Welcome to STOS Platform Admin"


stos_platform_admin = STOsPlatformAdminSite(name='stos_platform_admin')


# region User
class UserAdmin(admin.ModelAdmin):
    """Admin customization for User model."""
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')

    def has_delete_permission(self, request, obj=None):
        """Disable delete permission for User model."""
        return False


stos_platform_admin.register(User, UserAdmin)


# endregion


# region Filters
class TagsFilter(admin.SimpleListFilter):
    """Base class for custom tag filters."""
    title = 'Tags'
    parameter_name = 'tags'

    def get_tag_lookups(self, model):
        tags = model.objects.exclude(tags__isnull=True).values_list('tags', flat=True)
        tags_set = {tag.strip() for tag_string in tags for tag in tag_string.split(',')}
        return [(tag, tag) for tag in tags_set]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__icontains=self.value())
        return queryset


class ExtendedPeriodicTaskTagsFilter(TagsFilter):
    """Custom filter for tags in ExtendedPeriodicTask."""

    def lookups(self, request, model_admin):
        return self.get_tag_lookups(ExtendedPeriodicTask)


class ConfigTagsFilter(TagsFilter):
    """Custom filter for tags in Config."""

    def lookups(self, request, model_admin):
        return self.get_tag_lookups(Config)


class CreatedByFilter(admin.SimpleListFilter):
    """Custom filter for 'created_by' field."""
    title = 'Created By'
    parameter_name = 'created_by'

    def lookups(self, request, model_admin):
        creators = User.objects.prefetch_related(
            Prefetch('periodic_tasks', queryset=ExtendedPeriodicTask.objects.only('id'))
        ).distinct()
        return [(user.id, user.username) for user in creators]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by_id=self.value())
        return queryset


# endregion


# region ExtendedPeriodicTask
class ExtendedPeriodicTaskAdmin(BaseAdmin, PeriodicTaskAdmin):
    """Admin customization for ExtendedPeriodicTask model."""
    list_display = PeriodicTaskAdmin.list_display + ('created_by', 'get_tags') + BaseAdmin.list_display
    list_filter = [CreatedByFilter, ExtendedPeriodicTaskTagsFilter, 'enabled', 'one_off',
                   'created_date'] + BaseAdmin.list_filter
    search_fields = PeriodicTaskAdmin.search_fields + ('tags', 'created_date')
    actions = PeriodicTaskAdmin.actions + BaseAdmin.actions
    fieldsets = PeriodicTaskAdmin.fieldsets + (
        (None, {'fields': ('tags',)}),
    )

    def save_model(self, request, obj, form, change):
        """Assign 'created_by' to the user who creates a new task."""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_tags(self, obj):
        """Retrieve tags as a comma-separated string."""
        tags = obj.get_tags()
        return ', '.join(tags) if tags else '-'

    get_tags.short_description = 'Tags'


stos_platform_admin.register(ExtendedPeriodicTask, ExtendedPeriodicTaskAdmin)
stos_platform_admin.register(IntervalSchedule, IntervalScheduleAdmin)
stos_platform_admin.register(CrontabSchedule, CrontabScheduleAdmin)
stos_platform_admin.register(SolarSchedule, SolarScheduleAdmin)
stos_platform_admin.register(ClockedSchedule, ClockedScheduleAdmin)


# endregion


# region Holiday
class HolidayAdmin(BaseAdmin):
    """Admin customization for Holiday model."""
    list_display = ('name', 'date',) + BaseAdmin.list_display
    list_filter = ['date', ] + BaseAdmin.list_filter
    search_fields = ('name',)
    ordering = ['date']


stos_platform_admin.register(Holiday, HolidayAdmin)


# endregion


# region Config
class ConfigAdmin(BaseAdmin):
    """Admin customization for Config model."""
    list_display = ('key', 'value', 'get_tags') + BaseAdmin.list_display
    list_filter = ['key', 'tags'] + BaseAdmin.list_filter
    search_fields = ('key', 'value',)

    def get_tags(self, obj):
        """Retrieve tags for the config."""
        tags = obj.get_tags()
        return ', '.join(tags) if tags else '-'

    get_tags.short_description = 'Tags'


stos_platform_admin.register(Config, ConfigAdmin)
# endregion
