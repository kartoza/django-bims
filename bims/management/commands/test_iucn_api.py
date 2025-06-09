import json

from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from bims.utils import iucn
from bims.models.taxonomy import Taxonomy


class Command(BaseCommand):
    help = "Test IUCN API functions within a specific tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema', required=True,
            help='Tenant schema name (e.g. sa_namibia)'
        )
        parser.add_argument(
            '--assessment-id', type=int,
            help='IUCN Assessment ID to test get_assessment_detail'
        )
        parser.add_argument(
            '--habitat-code', type=str,
            help='Habitat code to test fetch_taxa'
        )
        parser.add_argument(
            '--taxon-id', type=int,
            help='Taxonomy model ID to test get_iucn_status'
        )

    def handle(self, *args, **options):
        schema_name = options['schema']
        TenantModel = get_tenant_model()

        try:
            tenant = TenantModel.objects.get(schema_name=schema_name)
        except TenantModel.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Tenant with schema '{schema_name}' not found."))
            return

        with schema_context(schema_name):
            self.stdout.write(self.style.SUCCESS(f"Using tenant schema: {schema_name}"))

            assessment_id = options.get('assessment_id')
            habitat_code = options.get('habitat_code')
            taxon_id = options.get('taxon_id')

            if assessment_id:
                self.stdout.write(self.style.NOTICE(f'Testing get_assessment_detail({assessment_id})...'))
                data = iucn.get_assessment_detail(assessment_id)
                self.stdout.write(self.style.SUCCESS(str(json.dumps(data, indent=4))))

            if habitat_code:
                self.stdout.write(self.style.NOTICE(f'Testing fetch_taxa("{habitat_code}")...'))
                data = iucn.fetch_taxa(habitat_code)
                self.stdout.write(self.style.SUCCESS(str(json.dumps(data, indent=4))))

            if taxon_id:
                try:
                    taxon = Taxonomy.objects.get(id=taxon_id)
                    self.stdout.write(self.style.NOTICE(f'Testing get_iucn_status(taxon={taxon})...'))
                    status, sis_id, url = iucn.get_iucn_status(taxon)
                    self.stdout.write(self.style.SUCCESS(f"IUCN Status: {status}, SIS ID: {sis_id}, URL: {url}"))
                except Taxonomy.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Taxonomy with ID {taxon_id} not found."))
