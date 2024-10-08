from django.contrib import admin
from django.db.models import Prefetch
from django_celery_beat.admin import (
    PeriodicTaskAdmin,
    IntervalScheduleAdmin,
    CrontabScheduleAdmin,
    SolarScheduleAdmin,
    ClockedScheduleAdmin
)
from django_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)

from core.base.admin import BaseAdmin
from .models import ExtendedPeriodicTask, User


class STOsPlatformAdminSite(admin.AdminSite):
    site_header = "STOS Platform Admin"
    site_title = "STOS Platform Admin"
    index_title = "Welcome to STOS Platform Admin"


stos_platform_admin = STOsPlatformAdminSite(name='stos_platform_admin')


# region User
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')

    def has_delete_permission(self, request, obj=None):
        # Disable delete permission
        return False


stos_platform_admin.register(User, UserAdmin)


# endregion

# region Tools Periodic Task
class TagsFilter(admin.SimpleListFilter):
    title = 'Tags'
    parameter_name = 'tags'

    def lookups(self, request, model_admin):
        tags = ExtendedPeriodicTask.objects.exclude(tags__isnull=True).values_list('tags', flat=True)
        tags_set = {tag.strip() for tag_string in tags for tag in tag_string.split(',')}
        return [(tag, tag) for tag in tags_set]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__icontains=self.value())
        return queryset


class CreatedByFilter(admin.SimpleListFilter):
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


class ExtendedPeriodicTaskAdmin(PeriodicTaskAdmin, BaseAdmin):
    list_display = PeriodicTaskAdmin.list_display + ('created_by', 'get_tags')
    list_filter = [CreatedByFilter, TagsFilter, 'enabled', 'one_off', 'created_date']
    search_fields = PeriodicTaskAdmin.search_fields + ('tags', 'created_date')
    fieldsets = PeriodicTaskAdmin.fieldsets + (
        (None, {'fields': ('tags',)}),
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
stos_platform_admin.register(IntervalSchedule, IntervalScheduleAdmin)
stos_platform_admin.register(CrontabSchedule, CrontabScheduleAdmin)
stos_platform_admin.register(SolarSchedule, SolarScheduleAdmin)
stos_platform_admin.register(ClockedSchedule, ClockedScheduleAdmin)
# endregion
