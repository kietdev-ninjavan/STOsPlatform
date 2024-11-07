from django.apps import AppConfig

from core.celery import app


class FailPickupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fail_pickup'

    def ready(self):
        from .handler.fail_process import fail_job_task
        app.autodiscover_tasks(fail_job_task)
