import os

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('STOsPlatform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# Ensure logging is set up properly for Celery
@after_setup_logger.connect
def setup_celery_logging(logger, *args, **kwargs):
    from django.conf import settings
    from logging.config import dictConfig

    dictConfig(settings.LOGGING)


@after_setup_task_logger.connect
def setup_task_logging(logger, *args, **kwargs):
    from django.conf import settings
    from logging.config import dictConfig

    dictConfig(settings.LOGGING)
