import uuid
from django.core.management.base import BaseCommand
from bims.models import BiologicalCollectionRecord
from django_tenants.utils import get_tenant_model, schema_context


class Command(BaseCommand):
    help = "Add missing UUIDs to BiologicalCollectionRecord entries"

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='The tenant schema to process',
        )
        parser.add_argument(
            '--batch_size',
            type=int,
            default=1000,
            help='Number of records to process in each batch',
        )

    def handle(self, *args, **options):
        tenant_name = options['tenant']
        batch_size = options['batch_size']

        # Get the tenant model
        TenantModel = get_tenant_model()

        try:
            tenant = TenantModel.objects.get(
                schema_name=tenant_name)
        except TenantModel.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"Tenant {tenant_name} does not exist"))
            return

        with schema_context(tenant.schema_name):
            total_records = BiologicalCollectionRecord.objects.filter(
                uuid__isnull=True).count()
            if total_records == 0:
                self.stdout.write(self.style.SUCCESS("No records are missing UUIDs"))
                return

            self.stdout.write(
                f"Processing {total_records} records in batches of {batch_size}")

            for start in range(0, total_records, batch_size):
                queryset = BiologicalCollectionRecord.objects.filter(
                    uuid__isnull=True)[start:start + batch_size]
                updates = []

                for record in queryset:
                    record.uuid = str(uuid.uuid4())
                    updates.append(record)

                BiologicalCollectionRecord.objects.bulk_update(updates, ['uuid'])
                self.stdout.write(
                    self.style.SUCCESS(f"Processed records {start + 1} to {start + len(updates)}")
                )

            self.stdout.write(
                self.style.SUCCESS("UUID assignment completed successfully")
            )
