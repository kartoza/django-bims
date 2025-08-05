# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from sass.models import SiteVisit
from sass.scripts.site_visit_ecological_condition_generator import (
    generate_site_visit_ecological_condition
)


class Command(BaseCommand):
    help = "Generate site visit ecological conditions. Supports multi-tenant schemas via --tenant."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help="Target schema name when using django-tenants. If omitted, runs in current schema.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Only process SiteVisits that do not have ecological conditions.",
        )

    def handle(self, *args, **options) -> None:
        self.options = options
        schema = options.get("tenant")

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR("This command requires django-tenants but it is not available.")
                )
                sys.exit(1)

            tenant = self._get_tenant(schema)
            if not tenant:
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self.stdout.write(self.style.HTTP_INFO(f"Running in tenant schema: {schema}"))
                self._run_update(label=f"tenant '{schema}'")
        else:
            self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
            self._run_update(label="current schema")

    def _run_update(self, label: str) -> None:
        only_missing = self.options.get("only_missing")
        if only_missing:
            site_visits = SiteVisit.objects.filter(
                sitevisitecologicalcondition__isnull=True
            )
        else:
            site_visits = SiteVisit.objects.all()

        count = site_visits.count()
        self.stdout.write(self.style.WARNING(f"[{label}] Found {count} SiteVisit(s) to process."))

        try:
            generate_site_visit_ecological_condition(site_visits)
            self.stdout.write(self.style.SUCCESS(f"[{label}] Completed ecological condition generation."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[{label}] Failed to generate ecological conditions: {e}"))

    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None
