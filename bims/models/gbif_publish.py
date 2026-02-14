import json
from django.db import models, connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django_tenants.utils import schema_context, get_public_schema_name


class PublishPeriod(models.TextChoices):
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"
    CUSTOM = "CUSTOM", "Custom (cron)"


class GbifPublishConfig(models.Model):
    """Configuration for GBIF publishing credentials and settings."""
    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for this configuration (e.g., 'Production', 'Test')"
    )
    gbif_api_url = models.URLField(
        default="https://api.gbif-uat.org/v1",
        help_text="GBIF API URL: https://api.gbif.org/v1 (production), "
                  "https://api.gbif-uat.org/v1 (UAT), "
                  "https://api.gbif-test.org/v1 (test). "
                  "Ensure credentials match the environment."
    )
    license_url = models.URLField(
        default="https://creativecommons.org/publicdomain/zero/1.0/legalcode",
        help_text="License URL for the dataset"
    )
    export_base_url = models.URLField(
        blank=True,
        help_text="Base URL where DwC-A exports will be accessible (e.g., https://yoursite.com)"
    )
    username = models.CharField(
        max_length=255,
        help_text="GBIF username for authentication"
    )
    password = models.CharField(
        max_length=255,
        help_text="GBIF password for authentication"
    )
    publishing_org_key = models.CharField(
        max_length=64,
        help_text="GBIF Publishing Organization Key (UUID)"
    )
    installation_key = models.CharField(
        max_length=64,
        help_text="GBIF Installation Key (UUID)",
        blank=True,
        default="",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "GBIF Publish Config"
        verbose_name_plural = "GBIF Publish Configs"

    def __str__(self):
        return f"{self.name} ({self.gbif_api_url})"


class GbifPublish(models.Model):
    module_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
        related_name="gbif_publish_schedules"
    )
    gbif_config = models.ForeignKey(
        GbifPublishConfig,
        on_delete=models.PROTECT,
        related_name="publish_schedules",
        help_text="GBIF configuration to use for publishing"
    )
    enabled = models.BooleanField(default=False)

    period = models.CharField(
        max_length=10,
        choices=PublishPeriod.choices,
        default=PublishPeriod.DAILY)
    run_at = models.TimeField(
        null=True, blank=True)
    day_of_week = models.CharField(
        max_length=9, blank=True)
    day_of_month = models.PositiveSmallIntegerField(
        null=True, blank=True)
    cron_expression = models.CharField(
        max_length=100, blank=True, default="")
    timezone = models.CharField(
        max_length=64, default="UTC")

    last_publish = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "GBIF Publish Schedule"
        verbose_name_plural = "GBIF Publish Schedules"

    def __str__(self):
        return f"GBIF Publish[{self.module_group_id}] - {self.period}"


class PublishTrigger(models.TextChoices):
    MANUAL = "manual", "Manual"
    SCHEDULED = "scheduled", "Scheduled"


class PublishStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"
    NO_RECORDS = "no_records", "No Records"


class GbifPublishSession(models.Model):
    """Stores results of each GBIF publish run."""
    schedule = models.ForeignKey(
        GbifPublish,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The publish schedule that triggered this session"
    )
    module_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gbif_publish_sessions"
    )
    gbif_config = models.ForeignKey(
        GbifPublishConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.PENDING
    )
    trigger = models.CharField(
        max_length=10,
        choices=PublishTrigger.choices,
        default=PublishTrigger.MANUAL
    )

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    dataset_key = models.CharField(
        max_length=64,
        blank=True,
        help_text="GBIF dataset UUID returned after successful registration"
    )
    records_published = models.PositiveIntegerField(
        default=0,
        help_text="Number of records published in this session"
    )
    archive_url = models.URLField(
        blank=True,
        help_text="URL to the DwC-A archive file"
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if the publish failed"
    )
    log_file = models.FileField(
        upload_to='gbif-publish-session-log/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "GBIF Publish Session"
        verbose_name_plural = "GBIF Publish Sessions"
        ordering = ["-start_time"]

    def __str__(self):
        return f"Publish Session {self.id} - {self.status} ({self.start_time})"

    @property
    def duration(self):
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None


def _mins_hrs(t):
    return (str(t.minute), str(t.hour)) if t else ("0", "2")


@receiver(post_delete, sender=GbifPublish)
def gbif_publish_post_delete(sender, instance: GbifPublish, **kwargs):
    schema = str(connection.schema_name)
    with schema_context(get_public_schema_name()):
        PeriodicTask.objects.filter(args=json.dumps([schema, instance.id])).delete()


@receiver(post_save, sender=GbifPublish)
def sync_gbif_publish_periodic_task(sender, instance: GbifPublish, **kwargs):
    name = f"GBIF publish: taxon_group={instance.module_group_id} id={instance.id}"

    if instance.period == PublishPeriod.CUSTOM and instance.cron_expression:
        m, h, dom, mon, dow = (instance.cron_expression.split() + ["*"]*5)[:5]
        cron_params = dict(minute=m, hour=h, day_of_month=dom, month_of_year=mon, day_of_week=dow)
    else:
        minute, hour = _mins_hrs(instance.run_at)
        if instance.period == PublishPeriod.DAILY:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week="*",
                day_of_month="*",
                month_of_year="*")
        elif instance.period == PublishPeriod.WEEKLY:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week=(instance.day_of_week or "mon"),
                day_of_month="*", month_of_year="*")
        elif instance.period == PublishPeriod.MONTHLY:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week="*",
                day_of_month=str(instance.day_of_month or 1),
                month_of_year="*")
        else:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week="*",
                day_of_month="*",
                month_of_year="*")

    schema = str(connection.schema_name)

    with schema_context(get_public_schema_name()):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            timezone=instance.timezone, **cron_params
        )
        PeriodicTask.objects.update_or_create(
            name=name,
            queue='update',
            defaults={
                "task": "bims.tasks.gbif_publish.run_scheduled_gbif_publish",
                "crontab": crontab,
                "args": json.dumps([schema, instance.id]),
                "enabled": instance.enabled,
            },
        )
