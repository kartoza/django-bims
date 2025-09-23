# core/management/commands/sync_celery_beat_schedule.py
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context, get_public_schema_name
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule, ClockedSchedule
from celery.schedules import crontab
from datetime import datetime, timedelta

def ensure_interval(every_seconds: int) -> IntervalSchedule:
    return IntervalSchedule.objects.get_or_create(
        every=int(every_seconds),
        period=IntervalSchedule.SECONDS,
    )[0]

def ensure_crontab(spec: crontab, tz: str) -> CrontabSchedule:
    # Works for either raw strings or celery’s sfield objects
    return CrontabSchedule.objects.get_or_create(
        minute=str(getattr(spec, "_orig_minute", spec.minute)),
        hour=str(getattr(spec, "_orig_hour", spec.hour)),
        day_of_week=str(getattr(spec, "_orig_day_of_week", spec.day_of_week)),
        day_of_month=str(getattr(spec, "_orig_day_of_month", spec.day_of_month)),
        month_of_year=str(getattr(spec, "_orig_month_of_year", spec.month_of_year)),
        timezone=tz or "UTC",
    )[0]

class Command(BaseCommand):
    help = "Sync CELERY_BEAT_SCHEDULE dict into django-celery-beat tables (public schema)."

    def handle(self, *args, **opts):
        beat_sched = getattr(settings, "CELERY_BEAT_SCHEDULE", {})
        tz = getattr(settings, "CELERY_TIMEZONE", "UTC")

        with schema_context(get_public_schema_name()):
            created, updated = 0, 0
            for name, entry in beat_sched.items():
                task = entry["task"]
                schedule = entry["schedule"]
                args = json.dumps(entry.get("args", ()))
                kwargs = json.dumps(entry.get("kwargs", {}))
                options = entry.get("options", {}) or {}

                pt_defaults = {
                    "task": task,
                    "args": args,
                    "kwargs": kwargs,
                    "queue": options.get("queue"),
                    "expires": options.get("expires"),
                    "one_off": options.get("one_off", False),
                    "enabled": True,
                    "description": options.get("description", ""),
                }

                # Attach the right schedule relation
                if isinstance(schedule, crontab):
                    pt_defaults["crontab"] = ensure_crontab(schedule, tz)
                    pt_defaults["interval"] = None
                    pt_defaults["clocked"] = None
                elif isinstance(schedule, timedelta) or isinstance(schedule, (int, float)):
                    seconds = int(schedule.total_seconds()) if isinstance(schedule, timedelta) else int(schedule)
                    pt_defaults["interval"] = ensure_interval(seconds)
                    pt_defaults["crontab"] = None
                    pt_defaults["clocked"] = None
                elif isinstance(schedule, datetime):
                    clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=schedule)
                    pt_defaults["clocked"] = clocked
                    pt_defaults["one_off"] = True
                    pt_defaults["interval"] = None
                    pt_defaults["crontab"] = None
                else:
                    self.stderr.write(self.style.WARNING(f"Skip '{name}': unsupported schedule type {type(schedule)}"))
                    continue

                obj, was_created = PeriodicTask.objects.update_or_create(name=name, defaults=pt_defaults)
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

            self.stdout.write(self.style.SUCCESS(f"Synced PeriodicTasks: created={created}, updated={updated}"))
