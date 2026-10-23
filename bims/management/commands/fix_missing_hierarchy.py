# coding=utf-8
"""Find (and fix where possible) taxa whose parent chain is broken.

Species placed under a subgenus point at the SUBGENUS row, not at the genus.
When that subgenus row has no parent, every higher rank (genus, family,
order, ...) is lost for all of its species even though sibling species that
sit directly under the genus are fine (e.g. Thraulus). The same happens when
a genus itself has no parent.

Fixes applied:
  * SUBGENUS without parent -> linked to the genus named in its canonical
    name "Genus (Subgenus)", or the genus of its first child species.
  * GENUS without parent -> linked to the family found in additional_data.

Anything that cannot be resolved automatically is reported only.
"""
import re

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:  # pragma: no cover - tenant support optional
    get_tenant_model = None
    schema_context = None

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

SUBGENUS_NAME_RE = re.compile(r'^\s*(?P<genus>[^\s(]+)\s*\(')
TOP_RANKS = ['KINGDOM', 'DOMAIN']
CHECKED_RANKS = ['GENUS', 'SUBGENUS', 'SPECIES', 'SUBSPECIES', 'VARIETY']


class Command(BaseCommand):
    help = (
        "Report taxa whose parent chain is missing suprageneric ranks and "
        "repair broken SUBGENUS/GENUS links. Supports --tenant/--all-tenants."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tenant", dest="tenant", default=None)
        parser.add_argument(
            "--all-tenants", dest="all_tenants", action="store_true",
            default=False,
        )
        parser.add_argument(
            "--dry-run", dest="dry_run", action="store_true", default=False,
            help="Report what would be fixed without saving.",
        )

    def handle(self, *args, **options):
        schema = options.get("tenant")
        if schema and options.get("all_tenants"):
            raise CommandError("Use either --tenant or --all-tenants, not both.")
        if schema or options.get("all_tenants"):
            if schema_context is None or get_tenant_model is None:
                raise CommandError("django-tenants is required for tenant iteration.")
            if schema:
                schemas = [schema]
            else:
                schemas = list(
                    get_tenant_model().objects.exclude(schema_name="public")
                    .values_list("schema_name", flat=True)
                )
            for name in schemas:
                with schema_context(name):
                    self.stdout.write(self.style.HTTP_INFO(f"Tenant schema: {name}"))
                    self._run(options)
            return
        self._run(options)

    def _run(self, options):
        dry_run = options["dry_run"]
        self._fix_subgenera(dry_run)
        self._fix_genera(dry_run)
        self._report_remaining()

    def _fix_subgenera(self, dry_run):
        from bims.models import Taxonomy

        fixed = unresolved = 0
        for sub in Taxonomy.objects.filter(rank__iexact='SUBGENUS', parent__isnull=True):
            genus = self._find_genus_for_subgenus(sub)
            if not genus:
                unresolved += 1
                self.stdout.write(self.style.WARNING(
                    f"  Subgenus {sub.canonical_name} (ID {sub.pk}): genus not found."
                ))
                continue
            self.stdout.write(
                f"  Subgenus {sub.canonical_name} (ID {sub.pk}) -> "
                f"genus {genus.canonical_name} (ID {genus.pk})"
            )
            fixed += 1
            if not dry_run:
                with transaction.atomic():
                    sub.parent = genus
                    sub.save(update_fields=["parent"])
        self.stdout.write(self.style.SUCCESS(
            f"Subgenera: {'would fix' if dry_run else 'fixed'} {fixed}, "
            f"unresolved {unresolved}."
        ))

    def _find_genus_for_subgenus(self, sub):
        from bims.models import Taxonomy

        names = []
        match = SUBGENUS_NAME_RE.match(sub.canonical_name or '')
        if match:
            names.append(match.group('genus'))
        child = Taxonomy.objects.filter(parent=sub).exclude(
            canonical_name=''
        ).first()
        if child:
            names.append(child.canonical_name.split(' ')[0])
        for name in names:
            genus = Taxonomy.objects.filter(
                rank__iexact='GENUS', canonical_name__iexact=name
            ).exclude(taxonomic_status__icontains='SYNONYM').first()
            if genus:
                return genus
        return None

    def _fix_genera(self, dry_run):
        from bims.models import Taxonomy

        fixed = unresolved = 0
        qs = Taxonomy.objects.filter(
            rank__iexact='GENUS', parent__isnull=True
        ).exclude(taxonomic_status__icontains='SYNONYM')
        for genus in qs:
            data = genus.additional_data if isinstance(genus.additional_data, dict) else {}
            family_name = data.get('Family') or data.get('family')
            family = family_name and Taxonomy.objects.filter(
                rank__iexact='FAMILY', canonical_name__iexact=family_name
            ).first()
            if not family:
                unresolved += 1
                self.stdout.write(self.style.WARNING(
                    f"  Genus {genus.canonical_name} (ID {genus.pk}): no parent, "
                    f"family cannot be resolved."
                ))
                continue
            self.stdout.write(
                f"  Genus {genus.canonical_name} (ID {genus.pk}) -> "
                f"family {family.canonical_name} (ID {family.pk})"
            )
            fixed += 1
            if not dry_run:
                with transaction.atomic():
                    genus.parent = family
                    genus.save(update_fields=["parent"])
        self.stdout.write(self.style.SUCCESS(
            f"Genera: {'would fix' if dry_run else 'fixed'} {fixed}, "
            f"unresolved {unresolved}."
        ))

    def _report_remaining(self):
        """List taxa whose parent chain stops before reaching the top."""
        from bims.models import Taxonomy

        broken = {}
        qs = Taxonomy.objects.filter(
            rank__in=CHECKED_RANKS
        ).exclude(taxonomic_status__icontains='SYNONYM').select_related('parent')
        for taxon in qs.iterator():
            seen, current = set(), taxon
            while current.parent_id and current.pk not in seen and len(seen) < 20:
                seen.add(current.pk)
                current = current.parent
            root_rank = (current.rank or '').upper()
            if root_rank not in TOP_RANKS:
                key = (taxon.canonical_name.split(' ')[0], root_rank,
                       current.canonical_name)
                broken[key] = broken.get(key, 0) + 1
        if not broken:
            self.stdout.write(self.style.SUCCESS("No broken parent chains."))
            return
        self.stdout.write(self.style.WARNING(
            "Chains that stop below the top (genus, chain ends at, taxa):"
        ))
        for (genus, rank, name), count in sorted(broken.items()):
            self.stdout.write(f"  {genus}: ends at {rank} {name} ({count})")
