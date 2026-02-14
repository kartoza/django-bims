# coding=utf-8
"""
GBIF Admin models - registered under a separate "GBIF Publishing" section
in the default Django admin site using proxy models.
"""
from django.contrib import admin, messages
from django.db import connection
from django.utils.html import format_html
from django.utils.timezone import localtime

from bims.models.gbif_publish import (
    PublishPeriod,
    GbifPublishConfig,
    GbifPublish,
    GbifPublishSession,
)
from bims.forms.gbif_publish import GbifPublishAdminForm
from bims.tasks import run_scheduled_gbif_publish


# Proxy models with custom app_label for admin grouping
class GbifPublishConfigProxy(GbifPublishConfig):
    class Meta:
        proxy = True
        verbose_name = 'GBIF Config'
        verbose_name_plural = 'GBIF Configs'


class GbifPublishProxy(GbifPublish):
    class Meta:
        proxy = True
        verbose_name = 'GBIF Publish Schedule'
        verbose_name_plural = 'GBIF Publish Schedules'


class GbifPublishSessionProxy(GbifPublishSession):
    class Meta:
        proxy = True
        verbose_name = 'GBIF Publish Session'
        verbose_name_plural = 'GBIF Publish Sessions'


@admin.register(GbifPublishConfigProxy)
class GbifPublishConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "gbif_api_url",
        "publishing_org_key",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "gbif_api_url", "publishing_org_key")
    readonly_fields = ("created_at", "updated_at")
    actions = ["create_new_installation"]

    fieldsets = (
        ("General", {
            "fields": ("name", "is_active"),
        }),
        ("GBIF API Settings", {
            "fields": (
                "gbif_api_url",
                "username",
                "password",
                "publishing_org_key",
                "installation_key",
            ),
        }),
        ("Dataset Settings", {
            "fields": ("license_url", "export_base_url"),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.action(description="Create new installation")
    def create_new_installation(self, request, queryset):
        from bims.utils.gbif_publish import create_new_installation
        obj = queryset.first()
        installation_key = create_new_installation(
            obj
        )
        if installation_key:
            obj.installation_key = installation_key
            obj.save()
            self.message_user(
                request,
                f"Installation key created", messages.SUCCESS)
        else:
            self.message_user(
                request,
                f"Failed to create installation key", messages.ERROR)


@admin.register(GbifPublishProxy)
class GbifPublishAdmin(admin.ModelAdmin):
    form = GbifPublishAdminForm

    list_display = (
        "module_group",
        "gbif_config",
        "enabled",
        "period",
        "schedule_human",
        "timezone",
        "last_publish_local",
        "updated_at",
    )
    list_filter = ("enabled", "period", "timezone", "gbif_config")
    search_fields = ("module_group__name", "gbif_config__name")
    raw_id_fields = ("module_group",)
    readonly_fields = ("last_publish", "updated_at", "schedule_preview")
    actions = ["action_run_now", "action_enable", "action_disable"]

    fieldsets = (
        ("Target", {
            "fields": ("module_group", "gbif_config", "enabled"),
        }),
        ("When to run", {
            "fields": (
                "period",
                "run_at",
                "day_of_week",
                "day_of_month",
                "cron_expression",
                "timezone",
                "schedule_preview",
            ),
            "description": (
                "Daily/Weekly/Monthly use run_at (+ day fields). "
                "Custom uses standard 5-field cron: 'm h dom mon dow' (e.g. '15 */6 * * *'). "
                "Day of week accepts 'mon,tue' or '0-6' (0=Sunday)."
            ),
        }),
        ("Audit", {
            "fields": ("last_publish", "updated_at"),
        }),
    )

    def schedule_human(self, obj: GbifPublish):
        if obj.period == PublishPeriod.CUSTOM and obj.cron_expression:
            return obj.cron_expression
        if obj.period == PublishPeriod.DAILY:
            return f"Daily at {obj.run_at}"
        if obj.period == PublishPeriod.WEEKLY:
            return f"Weekly {obj.day_of_week or 'mon'} at {obj.run_at}"
        if obj.period == PublishPeriod.MONTHLY:
            return f"Monthly day {obj.day_of_month or 1} at {obj.run_at}"
        return "-"

    schedule_human.short_description = "Schedule"

    def last_publish_local(self, obj):
        return localtime(
            obj.last_publish
        ).strftime("%Y-%m-%d %H:%M") if obj.last_publish else "—"
    last_publish_local.short_description = "Last Publish"

    def schedule_preview(self, obj):
        text = self.schedule_human(obj)
        return format_html("<code>{}</code>", text) if text else "—"
    schedule_preview.short_description = "Schedule preview"

    @admin.action(description="Run now (enqueue Celery task)")
    def action_run_now(self, request, queryset):
        count = 0
        for publish in queryset:
            schema_name = str(connection.schema_name)
            run_scheduled_gbif_publish.delay(schema_name, publish.id)
            count += 1
        self.message_user(
            request, f"Queued {count} publish job(s).", messages.SUCCESS)

    @admin.action(description="Enable schedule")
    def action_enable(self, request, queryset):
        updated = queryset.update(enabled=True)
        self.message_user(
            request, f"Enabled {updated} schedule(s).", messages.SUCCESS)

    @admin.action(description="Disable schedule")
    def action_disable(self, request, queryset):
        updated = queryset.update(enabled=False)
        self.message_user(
            request, f"Disabled {updated} schedule(s).", messages.SUCCESS)


@admin.register(GbifPublishSessionProxy)
class GbifPublishSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "schedule",
        "module_group",
        "status",
        "trigger",
        "dataset_key_short",
        "records_published",
        "start_time",
        "duration_display",
    )
    list_filter = ("status", "trigger", "module_group", "gbif_config")
    search_fields = ("dataset_key", "error_message", "schedule__module_group__name")
    readonly_fields = (
        "schedule",
        "module_group",
        "gbif_config",
        "status",
        "trigger",
        "start_time",
        "end_time",
        "dataset_key",
        "records_published",
        "archive_url",
        "error_message",
        "log_file",
        "duration_display",
    )
    ordering = ("-start_time",)

    fieldsets = (
        ("Session Info", {
            "fields": ("schedule", "module_group", "gbif_config", "trigger"),
        }),
        ("Status", {
            "fields": ("status", "start_time", "end_time", "duration_display"),
        }),
        ("Results", {
            "fields": ("dataset_key", "records_published", "archive_url"),
        }),
        ("Errors & Logs", {
            "fields": ("error_message", "log_file"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def dataset_key_short(self, obj):
        if obj.dataset_key:
            return obj.dataset_key[:8] + "..."
        return "—"
    dataset_key_short.short_description = "Dataset Key"

    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}m {seconds}s"
        return "—"
    duration_display.short_description = "Duration"
