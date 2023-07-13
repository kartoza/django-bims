import csv
import io
import os

from celery import shared_task
from django.core.cache import cache
from django.db.models import Value
from django.db.models.functions import Replace

from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.decision_support_tool import DecisionSupportTool
from bims.models.decision_support_tool_name import (
    DecisionSupportToolName
)


@shared_task(name='bims.tasks.process_decision_support_tool', queue='update')
def process_decision_support_tool(dst_file_path):
    errors_data = []
    messages = []
    created = 0
    error_file = ''

    with open(dst_file_path, 'rb') as dst_file:
        total_rows = (sum(1 for row in dst_file)) - 1

    with open(dst_file_path, 'rb') as dst_file:
        decoded_file = dst_file.read().decode('utf-8')
        dialect = csv.Sniffer().sniff(decoded_file, delimiters=";,")
        io_string = io.StringIO(decoded_file)

    line_count = 0
    bios = BiologicalCollectionRecord.objects.annotate(
        uuid_string=Replace('uuid', Value('-'), Value(''))
    )

    for line in csv.reader(io_string, delimiter=dialect.delimiter):
        if line_count == 0:
            print(f'Column names are {", ".join(line)}')
            line_count += 1
        else:
            uuid = line[0].replace('\n', '').strip().replace('-', '')
            name = line[1].replace('\n', '').strip()

            cache.set('DST_PROCESS', {
                'state': 'PROCESSING',
                'status': 'Processing {0}/{1}'.format(
                    line_count - 1, total_rows),
                'error_file': error_file
            })

            try:
                bio = bios.get(
                    uuid_string=uuid
                )
            except BiologicalCollectionRecord.DoesNotExist:
                errors_data.append([
                    uuid, name, 'Collection Record not found.'
                ])
                continue

            try:
                dst_name, _ = (
                    DecisionSupportToolName.objects.update_or_create(
                        name=name
                    )
                )
                dst, dst_created = (
                    DecisionSupportTool.objects.get_or_create(
                        biological_collection_record=bio,
                        dst_name=dst_name
                    )
                )
            except DecisionSupportTool.MultipleObjectsReturned:
                continue

            if dst_created:
                created += 1

            print(
                f'\t{uuid} DST for {name}')
            line_count += 1

    if created > 0:
        messages.append(f'{created} records added.')
    else:
        messages.append(f'No records added.')
    if errors_data:
        error_file = dst_file_path.replace('.csv', '_errors.csv')
        with open(
            error_file
        , 'w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['UUID', 'DST', 'Error'])
            for error in errors_data:
                writer.writerow(error)

        messages.append(f'Total error : {len(errors_data)}')

    cache.set('DST_PROCESS', {
        'state': 'FINISHED',
        'status': ' '.join(messages),
        'error_file': error_file
    })

    os.remove(dst_file_path)
