from bims.models import SourceReference, BiologicalCollectionRecord
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ids',
            dest='ids',
            default='',
            help='Source reference ids to be merged'
        )
        parser.add_argument(
            '-c',
            '--correct-id',
            dest='correct_id',
            default='',
        )

    def handle(self, *args, **options):
        correct_id = options.get('correct_id', '')
        if not correct_id:
            return
        correct_source_reference = SourceReference.objects.get(
            id=correct_id
        )
        source_references = SourceReference.objects.filter(
            id__in=options.get('ids', '').split(',')
        )
        if not source_references.exists():
            print('Source references not found')
            return

        bio = BiologicalCollectionRecord.objects.filter(
            source_reference__in=source_references
        )
        print(bio.count())
        bio.update(source_reference=correct_source_reference)
        SourceReference.objects.filter(
            id__in=source_references.values('id')
        ).exclude(id=correct_source_reference.id).delete()
