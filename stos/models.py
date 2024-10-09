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


class Holiday(BaseModel):
    name = models.CharField(max_length=255, help_text="The name of the holiday.")
    date = models.DateField(unique=True, help_text="The date of the holiday.")

    def __str__(self):
        return f"{self.name} ({self.date})"

    class Meta:
        ordering = ['date']
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        indexes = [
            models.Index(fields=['date']),
        ]
