# filters.py

import logging
import re

from django.apps import apps


class AppQueryFilter(logging.Filter):
    """
    A logging filter that only allows logging of queries related to specific Django apps.
    """

    def __init__(self, app_names):
        self.app_names = app_names
        super().__init__()

    def filter(self, record):
        # Collect all model table names for the specified apps
        app_models = []
        for app_name in self.app_names:
            app_config = apps.get_app_config(app_name)
            app_models += [model._meta.db_table for model in app_config.get_models()]

        # Check if the SQL query involves any tables related to the apps' models
        for model_table in app_models:
            if re.search(rf'\b{model_table}\b', record.sql):
                return True
        return False
