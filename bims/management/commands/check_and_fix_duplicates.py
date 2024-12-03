import uuid
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django_tenants.utils import get_tenant_model, schema_context
from bims.models import BiologicalCollectionRecord


class Command(BaseCommand):
    help = "Check and fix duplicate UUIDs in BiologicalCollectionRecord for all tenants."

    def handle(self, *args, **kwargs):
        Tenant = get_tenant_model()
        tenants = Tenant.objects.all()

        for tenant in tenants:
            self.stdout.write(f"Processing tenant: {tenant.schema_name}")

            with schema_context(tenant.schema_name):
                self.check_and_fix_duplicates()

        self.stdout.write("Duplicate UUID check and fix completed.")

    def check_and_fix_duplicates(self):
        duplicates = (
            BiologicalCollectionRecord.objects.values("uuid")
            .annotate(count=models.Count("uuid"))
            .filter(count__gt=1)
        )

        if duplicates.exists():
            self.stdout.write(f"Found duplicates: {len(duplicates)}")

            for duplicate in duplicates:
                duplicate_uuid = duplicate["uuid"]
                self.stdout.write(f"Fixing duplicate UUID: {duplicate_uuid}")

                with transaction.atomic():
                    records = BiologicalCollectionRecord.objects.filter(uuid=duplicate_uuid)
                    for idx, record in enumerate(records):
                        if idx > 0:
                            new_uuid = uuid.uuid4()
                            self.stdout.write(f"Updating record {record.id} with new UUID: {new_uuid}")
                            record.uuid = new_uuid
                            record.save(update_fields=["uuid"])
        else:
            self.stdout.write("No duplicates found.")
