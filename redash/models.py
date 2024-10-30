from django.db import models

from core.base.model import BaseModel


class StatusChoices(models.IntegerChoices):
    PENDING = 1, 'Pending'
    RUNNING = 2, 'Running'
    SUCCESS = 3, 'Success'
    FAILURE = 4, 'Failure'
    CANCELLED = 5, 'Cancelled'


class Job(BaseModel):
    job_id = models.CharField(max_length=36, primary_key=True)
    query_id = models.IntegerField()
    status = models.IntegerField(choices=StatusChoices.choices, default=StatusChoices.PENDING)
    error = models.TextField(null=True, blank=True)
    result_id = models.BigIntegerField(null=True)
