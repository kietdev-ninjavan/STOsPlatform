from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    def get_queryset(self):
        # Override the default queryset to only return active objects
        return super().get_queryset().filter(delete_at__isnull=True)


# Base Model
class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    delete_at = models.DateTimeField(null=True)  # Soft delete field

    objects = ActiveManager()  # Custom manager to handle active (non-deleted) objects
    all_objects = models.Manager()  # Default manager to access all objects including soft-deleted ones

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """
        Override delete method to perform soft delete by setting delete_at=now.
        instead of actually deleting the object.
        """
        self.delete_at = timezone.now()
        self.save()

    def restore(self):
        """
        Restore a soft-deleted object by setting delete_at=None.
        """
        self.delete_at = None
        self.save()
