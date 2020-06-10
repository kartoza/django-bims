# coding=utf-8
import os
import json
from celery import shared_task
from django.conf import settings
from bims.utils.celery import single_instance_task
from bims.utils.logger import log
from bims.models.source_reference import (
    SourceReference
)

SOURCE_REFERENCE_FILTER_FILE = 'source_reference_filter.txt'


@shared_task(
    name='bims.tasks.generate_source_reference_filter',
    queue='update')
@single_instance_task(60 * 10)
def generate_source_reference_filter(file_path=None):
    references = SourceReference.objects.filter(
        biologicalcollectionrecord__isnull=False,
    ).distinct('id')
    results = []
    reference_source_list = []
    for reference in references:
        if (
            reference.reference_type == 'Peer-reviewed scientific article' or
            reference.reference_type == 'Published report or thesis'
        ):
            source = u'{authors} | {year} | {title}'.format(
                authors=reference.authors,
                year=reference.year,
                title=reference.title
            )
        else:
            source = str(reference.source)
        if source not in reference_source_list:
            reference_source_list.append(source)
        else:
            continue
        results.append(
            {
                'id': reference.id,
                'reference': source,
                'type': reference.reference_type
            }
        )
    if not file_path:
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            SOURCE_REFERENCE_FILTER_FILE
        )
    log(file_path)
    with open(file_path, 'w') as file_handle:
        json.dump(results, file_handle)


def get_source_reference_filter():
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        SOURCE_REFERENCE_FILTER_FILE
    )
    if not os.path.exists(file_path):
        generate_source_reference_filter(file_path)
    with open(file_path, 'r') as file_handler:
        filter_data = file_handler.read()
    if filter_data:
        return json.loads(filter_data)
    else:
        return []
