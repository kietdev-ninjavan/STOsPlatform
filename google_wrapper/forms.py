from django import forms

from .models import ServiceAccount


class GoogleServiceAccountForm(forms.ModelForm):
    private_key = forms.CharField(widget=forms.Textarea, help_text="Paste the private key here.")

    class Meta:
        model = ServiceAccount
        fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id',
                  'auth_uri', 'token_uri', 'auth_provider_x509_cert_url', 'universe_domain']

    def save(self, commit=True):
        # Get the instance, but don't save it yet
        instance = super().save(commit=False)

        # If the form includes a private_key field, set it using the setter, which encrypts the value
        if 'private_key' in self.cleaned_data:
            instance.private_key = self.cleaned_data['private_key']

        # Save the instance if requested
        if commit:
            instance.save()
        return instance
