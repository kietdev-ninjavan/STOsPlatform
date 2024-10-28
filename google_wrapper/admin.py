import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path

from core.base.admin import BaseAdmin
from stos.admin import stos_platform_admin
from .models import ServiceAccount


class GoogleServiceAccountAdmin(BaseAdmin):
    list_display = ('name', 'project_id', 'client_email', 'private_key_id') + BaseAdmin.list_display
    search_fields = ('project_id', 'client_email', 'private_key_id')

    exclude = ('name', 'auth_uri', 'token_uri', 'auth_provider_x509_cert_url', 'universe_domain') + BaseAdmin.exclude

    # Custom URL for "Create from JSON"
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-json/', self.admin_site.admin_view(self.create_from_json_view), name='create_from_json'),
        ]
        return custom_urls + urls

    # Custom view to handle JSON upload
    def create_from_json_view(self, request):
        if request.method == 'POST':
            json_file = request.FILES.get('json_file')
            if not json_file:
                messages.error(request, "No file uploaded. Please upload a valid JSON file.")
                return redirect('..')

            try:
                account_data = json.load(json_file)
                # Using update_or_create to either update an existing object or create a new one
                ServiceAccount.objects.update_or_create(
                    project_id=account_data['project_id'],  # Field(s) used to look for an existing record
                    defaults={
                        'private_key_id': account_data['private_key_id'],
                        '_private_key': account_data['private_key'],  # Correct field name in model
                        'client_email': account_data['client_email'],
                        'client_id': account_data['client_id'],
                    }
                )
                messages.success(request, "Service account has been successfully created or updated from JSON.")
                return redirect('..')
            except Exception as e:
                messages.error(request, f"Error processing the JSON file: {str(e)}")
                return redirect('..')

        # Render the upload form
        return render(request, 'admin/create_from_json.html')


stos_platform_admin.register(ServiceAccount, GoogleServiceAccountAdmin)
