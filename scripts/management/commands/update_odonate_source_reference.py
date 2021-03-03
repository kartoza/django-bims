from django.core.management.base import BaseCommand
from bims.models import (
    BiologicalCollectionRecord,
    SourceReferenceDatabase,
    TaxonGroup
)


class Command(BaseCommand):
    """This is to fix issue https://github.com/kartoza/django-bims/issues/2524"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--source-reference',
            dest='source_reference_name',
            default='OdonataMap Virtual Museum, FitzPatrick Institute of African Ornithology, University of Cape Town, 2021',
            help='Name of the source reference'
        )

    def handle(self, *args, **options):
        source_reference_name = options.get('source_reference_name', '')
        source_reference = None
        try:
            source_reference = SourceReferenceDatabase.objects.get(
                source__name=source_reference_name
            )
        except SourceReferenceDatabase.DoesNotExist():
            print('Source reference does not exist')

        taxon_modules = TaxonGroup.objects.filter(
            name__icontains='Odonate adult'
        )
        if taxon_modules.exists():
            module_group = taxon_modules[0]
            bio = BiologicalCollectionRecord.objects.filter(
                module_group=module_group
            ).exclude(source_reference=source_reference)
            print('Updating {} records'.format(bio.count()))
            bio.update(
                source_reference=source_reference
            )
            print('Finish updating')
