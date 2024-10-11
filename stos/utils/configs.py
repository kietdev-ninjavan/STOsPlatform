from core.patterns import SingletonMeta
from ..models import Config


class Configs(metaclass=SingletonMeta):
    def __init__(self):
        pass

    def get(self, key, default=None, cast=None):
        """
        Get a configuration value by key. Always loads from the database.
        """
        try:
            # Query the database for the specific key
            config = Config.objects.get(key=key)
            # cast the value to the specified type
            if cast:
                return cast(config.value)
            return config.value

        except Config.DoesNotExist:
            # Return default if key does not exist
            return default

    def set(self, key, value):
        """
        Set or update a configuration value in the database.
        """
        config, created = Config.objects.update_or_create(key=key, defaults={'value': value})
        return config
