import os
import csv
import json
from django.conf import settings
from django.db.models import Q
from django.core.management import BaseCommand
from bims.models import (
    BiologicalCollectionRecord,
    SourceReference,
    SourceReferenceBibliography,
    SourceReferenceDatabase,
    SourceReferenceDocument,
    ChemicalRecord
)


class Command(BaseCommand):

    csv_path = os.path.join(settings.MEDIA_ROOT, 'unpublished.csv')

    def export_to_csv(self):
        source_references = SourceReference.objects.all().exclude(
            Q(instance_of=SourceReferenceDatabase) |
            Q(instance_of=SourceReferenceBibliography) |
            Q(instance_of=SourceReferenceDocument)
        )
        with open(self.csv_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'source_reference_id',
                'source_reference_note',
                'source_reference_source_name',
                'bio', 'chems'])

            for source_reference in source_references:
                writer.writerow([
                    source_reference.id,
                    source_reference.note,
                    source_reference.source_name,
                    list(
                        BiologicalCollectionRecord.objects.filter(
                            source_reference=source_reference
                        ).values_list(
                            'id',
                            flat=True
                        )
                    ),
                    list(
                        ChemicalRecord.objects.filter(
                            source_reference=source_reference
                        ).values_list(
                            'id',
                            flat=True
                        )
                    )
                ])

    def import_from_csv(self):
        with open(self.csv_path, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                line_count += 1
                if line_count == 1:
                    continue
                source_reference_id = row[0]
                source_reference_note = row[1]
                source_reference_source_name = row[2]
                bios = BiologicalCollectionRecord.objects.filter(
                    id__in=json.loads(row[3])
                )
                chems = ChemicalRecord.objects.filter(
                    id__in=json.loads(row[4])
                )
                try:
                    source_reference = SourceReference.objects.get(
                        id=source_reference_id
                    )
                except SourceReference.DoesNotExists():
                    source_reference = SourceReference.objects.create(
                        note=source_reference_note,
                        source_name=source_reference_source_name
                    )
                bios.update(source_reference=source_reference)
                chems.update(source_reference=source_reference)
                print(source_reference, bios.count())

    def handle(self, *args, **options):
        self.import_from_csv()
