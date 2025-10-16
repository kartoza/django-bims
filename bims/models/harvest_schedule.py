import json
from django.db import models, connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django_tenants.utils import schema_context, get_public_schema_name


class HarvestPeriod(models.TextChoices):
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"
    CUSTOM = "CUSTOM", "Custom (cron)"


class HarvestSchedule(models.Model):
    module_group = models.OneToOneField(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
        related_name="harvest_schedule"
    )
    enabled = models.BooleanField(default=False)

    period = models.CharField(
        max_length=10,
        choices=HarvestPeriod.choices,
        default=HarvestPeriod.DAILY)
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

    harvest_synonyms_default = models.BooleanField(
        default=False,
        help_text="Harvest synonyms"
    )
    is_fetching_species = models.BooleanField(
        default=False,
        help_text="Harvest species"
    )
    boundary_default = models.ForeignKey(
        "bims.Boundary", null=True, blank=True, on_delete=models.SET_NULL
    )

    last_harvest_until = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule[{self.module_group_id}] {self.period}"


def _mins_hrs(t):
    return (str(t.minute), str(t.hour)) if t else ("0", "2")


@receiver(post_delete, sender=HarvestSchedule)
def harvest_schedule_post_delete(sender, instance: HarvestSchedule, **kwargs):
    schema = str(connection.schema_name)
    with schema_context(get_public_schema_name()):
        PeriodicTask.objects.filter(args=json.dumps([schema, instance.id])).delete()


@receiver(post_save, sender=HarvestSchedule)
def sync_periodic_task(sender, instance: HarvestSchedule, **kwargs):
    name = f"GBIF harvest: taxon_group={instance.module_group_id}"

    if instance.period == HarvestPeriod.CUSTOM and instance.cron_expression:
        m, h, dom, mon, dow = (instance.cron_expression.split() + ["*"]*5)[:5]
        cron_params = dict(minute=m, hour=h, day_of_month=dom, month_of_year=mon, day_of_week=dow)
    else:
        minute, hour = _mins_hrs(instance.run_at)
        if instance.period == HarvestPeriod.DAILY:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week="*",
                day_of_month="*",
                month_of_year="*")
        elif instance.period == HarvestPeriod.WEEKLY:
            cron_params = dict(
                minute=minute,
                hour=hour,
                day_of_week=(instance.day_of_week or "mon"),
                day_of_month="*", month_of_year="*")
        elif instance.period == HarvestPeriod.MONTHLY:
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
                "task": "bims.tasks.harvest_schedule.run_scheduled_gbif_harvest",
                "crontab": crontab,
                "args": json.dumps([schema, instance.id]),
                "enabled": instance.enabled,
            },
        )
