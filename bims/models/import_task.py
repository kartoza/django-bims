from django.db import models


class ImportTask(models.Model):
    MODULE_CHOICES = [
        ('odonates', 'Odonates'),
        ('anurans', 'Anurans'),
    ]

    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    start_index = models.IntegerField(default=0)
    total_records = models.IntegerField()
    in_progress = models.BooleanField(default=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    log_text = models.TextField(null=True, blank=True)
    cancel = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"ImportTask({self.module}, "
            f"{self.start_index}, "
            f"{self.total_records}, "
            f"{self.in_progress})"
        )
