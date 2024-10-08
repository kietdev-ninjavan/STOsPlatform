import json

from django.db import models

from core.base.model import BaseModel
from stos.utils import encrypt_value, decrypt_value


class ServiceAccount(BaseModel):
    type = models.CharField(max_length=255, default="service_account")
    name = models.CharField(max_length=255, db_index=True)
    project_id = models.CharField(max_length=255)
    private_key_id = models.CharField(max_length=255, primary_key=True)
    _private_key = models.TextField(db_column='private_key')  # Encrypted field
    client_email = models.EmailField(max_length=255)
    client_id = models.CharField(max_length=255)
    auth_uri = models.URLField(max_length=255, default="https://accounts.google.com/o/oauth2/auth")
    token_uri = models.URLField(max_length=255, default="https://oauth2.googleapis.com/token")
    auth_provider_x509_cert_url = models.URLField(max_length=255, default="https://www.googleapis.com/oauth2/v1/certs")
    universe_domain = models.CharField(max_length=255, default="googleapis.com")

    @property
    def private_key(self) -> str:
        """Decrypt the private_key when accessed."""
        return decrypt_value(self._private_key).replace('\\n', '\n')

    @private_key.setter
    def private_key(self, value: str):
        """Encrypt the private_key after validation and when setting."""
        # Validate the private key format
        if not value:
            raise ValueError("Private key must be set.")

        # Encrypt the valid private key
        self._private_key = encrypt_value(value)

    @property
    def client_x509_cert_url(self) -> str:
        """Construct client_x509_cert_url based on client_email."""
        return f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email.replace('@', '%40')}"

    def save(self, *args, **kwargs):
        """Override save method to ensure private_key is encrypted."""
        if not self._private_key:
            raise ValueError("Private key must be set.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Google Service Account: {self.project_id} ({self.client_email})"

    def to_dict(self):
        """Custom method to return a dictionary representation of the model, with decrypted private_key."""
        account_dict = {
            "type": self.type,
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,  # Decrypted private key
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": self.auth_uri,
            "token_uri": self.token_uri,
            "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
            "client_x509_cert_url": self.client_x509_cert_url,
            "universe_domain": self.universe_domain,
        }
        return account_dict

    def to_json(self):
        """Custom method to return a JSON representation of the model, with decrypted private_key."""
        return json.dumps(self.to_dict())
