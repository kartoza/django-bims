# coding=utf-8
"""
Management command to populate DataSource entries for a specific tenant.
Usage: python manage.py populate_tenant_data_sources [--tenant=fbis]
"""
from django.core.management.base import BaseCommand
from bims.models import DataSource


class Command(BaseCommand):
    help = 'Populate DataSource entries for the current or specified tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant name (e.g., fbis, sanparks)',
            default=None
        )

    def handle(self, *args, **options):
        from django.db import connection
        from bims.models import SiteSetting

        # Get project name from options, site setting, or schema
        project_name = options.get('tenant')

        if not project_name:
            # Try to get from site setting first
            try:
                site_setting = SiteSetting.load()
                project_name = site_setting.default_data_source if site_setting.default_data_source else None
            except Exception:
                project_name = None

        # Fallback to schema name if no site setting
        if not project_name:
            project_name = connection.schema_name
            if project_name == 'public':
                project_name = 'bims'

        self.stdout.write(f'Populating data sources for project: {project_name}')

        # Define data sources based on project
        if project_name == 'fbis':
            # FBIS-specific data sources
            data_sources = [
                {
                    'name': 'fbis',
                    'category': 'Primary',
                    'description': (
                        'Data not available via GBIF that have been sourced and collated from reputable '
                        'databases, peer-reviewed scientific articles, published reports, theses and other '
                        'unpublished data sources.'
                    )
                },
                {
                    'name': 'gbif',
                    'category': 'External',
                    'description': (
                        'Freshwater species occurrence data available for South Africa that are currently '
                        'available via the Global Biodiversity Information Facility (GBIF). GBIF includes '
                        'periodically-updated data from the South African Institute for Aquatic Biodiversity '
                        '(SAIAB), as well as \'Research Grade\' iNaturalist data (i.e. records from non-captive '
                        'individuals, with a picture, locality and date, and with two or more IDs in agreement '
                        'at species level). Invertebrate data includes both aquatic and aerial stages.'
                    )
                },
                {
                    'name': 'virtual_museum',
                    'category': 'External',
                    'description': (
                        'Freshwater species occurrence data for South Africa that are currently available at '
                        'Virtual Museum (VM) (<a href=\'https://vmus.adu.org.za/\' target=\'_blank\'>'
                        'https://vmus.adu.org.za/</a>). VM is a platform for citizen scientists to contribute '
                        'to biodiversity data and is managed by The Biodiversity and Development Institute '
                        '(<a href=\'http://thebdi.org/\' target=\'_blank\'>http://thebdi.org/</a>) and '
                        'The FitzPatrick Institute of African Ornithology '
                        '(<a href=\'http://www.fitzpatrick.uct.ac.za/\' target=\'_blank\'>'
                        'http://www.fitzpatrick.uct.ac.za/</a>).'
                    )
                },
            ]
        else:
            # For other projects, create project-specific and general GBIF sources
            data_sources = [
                {
                    'name': project_name,
                    'category': 'Primary',
                    'description': (
                        f'{project_name.upper()} project data - biodiversity occurrence records '
                        'collected and managed by the project.'
                    )
                },
                {
                    'name': 'gbif',
                    'category': 'External',
                    'description': (
                        'Global Biodiversity Information Facility (GBIF) - an international network '
                        'and data infrastructure providing access to biodiversity data from around the world.'
                    )
                },
            ]

        # Create or update data sources
        created_count = 0
        updated_count = 0

        for ds_data in data_sources:
            obj, created = DataSource.objects.update_or_create(
                name=ds_data['name'],
                defaults={
                    'category': ds_data['category'],
                    'description': ds_data['description']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created data source: {ds_data["name"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated data source: {ds_data["name"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created: {created_count}, Updated: {updated_count}'
            )
        )
