from django.contrib.auth.models import AbstractUser
from django.db import models
from django_celery_beat.models import PeriodicTask

from core.base.model import BaseModel


class User(AbstractUser):
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)


class ExtendedPeriodicTask(PeriodicTask, BaseModel):
    # Store tags as a comma-separated string
    tags = models.TextField(blank=True, null=True, help_text="Tags to categorize the task, separated by commas")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='periodic_tasks', )

    def get_tags(self):
        return self.tags.split(',') if self.tags else []

    def set_tags(self, tags_list):
        self.tags = ','.join(tags_list)

    class Meta:
        verbose_name = 'Tool Periodic Task'
        verbose_name_plural = 'Tool Periodic Tasks'
