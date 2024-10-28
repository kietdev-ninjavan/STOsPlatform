from ..models import ServiceAccount


def get_service_account(service_account_name: str) -> ServiceAccount:
    try:
        return ServiceAccount.objects.get(name=service_account_name)
    except ServiceAccount.DoesNotExist:
        raise Exception(f'Service account {service_account_name} not found in the database.')
