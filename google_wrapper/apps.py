import logging
import os
import sys
import time

from django.apps import AppConfig

# from threading import Thread

logger = logging.getLogger(__name__)


def start_pubsub_listener():
    while True:
        logger.info("Pub/Sub listener is running...")
        time.sleep(2)


class GoogleWrapperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'google_wrapper'

    def ready(self):
        # Check if the process is gunicorn or runserver
        if os.environ.get('RUN_MAIN') == 'true' or 'gunicorn' in sys.argv or '--noreload' in sys.argv:
            logger.info("Starting Pub/Sub listener in web server process...")
            # Thread(target=start_pubsub_listener, daemon=True).start()
        else:
            logger.info(f"Skipping Pub/Sub listener. Process: {sys.argv}")
