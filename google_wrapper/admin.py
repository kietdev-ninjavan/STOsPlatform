from django.contrib import admin

from .forms import GoogleServiceAccountForm
from .models import ServiceAccount


class GoogleServiceAccountAdmin(admin.ModelAdmin):
    form = GoogleServiceAccountForm
    list_display = ('project_id', 'client_email', 'private_key_id')  # Customize to display important fields
    search_fields = ('project_id', 'client_email', 'private_key_id')  # Enable searching by important fields


admin.site.register(ServiceAccount, GoogleServiceAccountAdmin)
