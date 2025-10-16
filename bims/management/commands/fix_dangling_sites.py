# bims/management/commands/fix_dangling_sites.py
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef, QuerySet
from django.db import transaction

from bims.models import LocationContext
from bims.models.location_site import LocationSite

# Only imported when the --tenant flag is used, so environments without
# django-tenants can still use the command.
try:
    from django_tenants.utils import schema_context, get_tenant_model
except ImportError:
    schema_context = None
    get_tenant_model = None


class Command(BaseCommand):
    """
    Find (and optionally delete) LocationSite rows that have **no**
    related objects anywhere in the database.

    Supports multi-tenant setups (django-tenants) via --tenant=<schema_name>.
    """

    help = (
        "Report (and optionally delete) LocationSite rows that have no related "
        "objects.  Use --tenant=<schema> to run inside a specific tenant "
        "schema."
    )

    # ---------------------------------------------------------------- arguments
    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the dangling rows after confirmation.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Print primary keys of dangling rows.",
        )
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help="Schema name of the tenant (django-tenants). If omitted, "
                 "the command runs in the current schema.",
        )

    # ---------------------------------------------------------------- handle
    def handle(self, *args, **opts):
        schema = opts.get("tenant")

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR(
                        "--tenant flag requires django-tenants to be installed."
                    )
                )
                return
            tenant = self._get_tenant(schema)
            if not tenant:
                return
            with schema_context(tenant.schema_name):
                self._run_in_schema(opts, schema)
        else:
            self._run_in_schema(opts, "current")

    # ------------------------------------------------------------- helpers
    def _run_in_schema(self, opts, label: str):
        """Core logic, executed inside the right schema."""
        dangling_qs = self._find_dangling()

        total = dangling_qs.count()
        self.stdout.write(
            self.style.SUCCESS(f"[{label}] dangling LocationSite rows: {total}")
        )

        if opts["list"] and total:
            ids = ", ".join(map(str, dangling_qs.values_list("pk", flat=True)))
            self.stdout.write(f"IDs: {ids}")

        if opts["delete"] and total and self._confirm():
            self._delete(dangling_qs, total)

    # ------------------------------------------------------- dangling finder
    @staticmethod
    def _find_dangling() -> QuerySet:
        """
        Keep a site only if *every* reverse relation (EXCEPT LocationContext)
        has zero matches.
        """
        qs = LocationSite.objects.all()

        for rel in LocationSite._meta.get_fields():
            if not (rel.auto_created and not rel.concrete):
                continue  # skip normal fields

            # ── skip LocationContext completely ───────────────────────────
            if rel.related_model is LocationContext:
                continue

            related_model = rel.related_model
            link_field = (
                rel.field.name
                if hasattr(rel, "field") and rel.field
                else rel.field.m2m_field_name()
            )
            sub = related_model.objects.filter(**{link_field: OuterRef("pk")})
            qs = qs.filter(~Exists(sub))

        return qs

    # -------------------------------------------------------- confirmation
    @staticmethod
    def _confirm() -> bool:
        return (
            input("Type 'yes' to delete dangling rows: ")
            .strip()
            .lower()
            == "yes"
        )

    @transaction.atomic
    def _delete(self, qs: QuerySet, total: int):
        deleted, _ = qs.delete()
        self.stdout.write(
            self.style.WARNING(f"Deleted {deleted}/{total} rows.")
        )

    # ------------------------------------------------ tenant resolution
    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None
