import base64
from hashlib import sha256

from cryptography.fernet import Fernet
from django.conf import settings


def get_encryption_key() -> bytes:
    """Derive an encryption key from Django's SECRET_KEY."""
    # Hash the SECRET_KEY to create a consistent encryption key
    key = sha256(settings.SECRET_KEY.encode()).digest()
    # Fernet requires a 32-byte base64-encoded key, so ensure it's the right format
    return base64.urlsafe_b64encode(key[:32])


def encrypt_value(value: str) -> str:
    """Encrypts a given string using Fernet symmetric encryption."""
    cipher_suite = Fernet(get_encryption_key())
    encrypted_value = cipher_suite.encrypt(value.encode())
    return encrypted_value.decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypts a given encrypted string using Fernet symmetric encryption."""
    cipher_suite = Fernet(get_encryption_key())
    decrypted_value = cipher_suite.decrypt(encrypted_value.encode())
    return decrypted_value.decode()
