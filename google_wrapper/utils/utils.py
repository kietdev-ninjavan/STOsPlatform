from ..models import ServiceAccount


def get_service_account(private_key_id: str) -> ServiceAccount:
    try:
        return ServiceAccount.objects.get(private_key_id=private_key_id)
    except ServiceAccount.DoesNotExist:
        raise Exception(f'Service account {private_key_id} not found in the database.')
