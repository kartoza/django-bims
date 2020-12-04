import csv
from bims.models import *

source_references = SourceReference.objects.all()

csv_file_path = os.path.join(settings.MEDIA_ROOT, 'source_references.csv')

with open(csv_file_path, mode='w') as csv_file:
    writer = csv.writer(
        csv_file, delimiter=',', quotechar='"',
        quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        'ID',
        'Title',
        'Type',
        'Author',
        'Records'
    ])
    for source_reference in source_references:
        if source_reference.reference_type == 'Unpublished data':
            continue
        records = BiologicalCollectionRecord.objects.filter(
            source_reference=source_reference
        ).count()
        writer.writerow([
            source_reference.id,
            source_reference.title,
            source_reference.reference_type,
            source_reference.authors,
            records
        ])
