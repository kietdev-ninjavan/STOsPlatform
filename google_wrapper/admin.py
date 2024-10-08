from core.base.admin import BaseAdmin
from stos.admin import stos_platform_admin
from .forms import GoogleServiceAccountForm
from .models import ServiceAccount


class GoogleServiceAccountAdmin(BaseAdmin):
    form = GoogleServiceAccountForm
    list_display = ('project_id', 'client_email', 'private_key_id')  # Customize to display important fields
    search_fields = ('project_id', 'client_email', 'private_key_id')  # Enable searching by important fields


stos_platform_admin.register(ServiceAccount, GoogleServiceAccountAdmin)
