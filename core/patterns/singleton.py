import threading


class SingletonMeta(type):
    """
    A thread-safe implementation of Singleton using a metaclass.
    This allows us to apply the singleton pattern to any class that uses this metaclass.
    """
    _instances = {}
    _lock = threading.Lock()  # Ensures thread-safe instance creation

    def __call__(cls, *args, **kwargs):
        # First, check if the instance already exists
        if cls not in cls._instances:
            with cls._lock:
                # Double-checked locking to avoid race conditions
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
