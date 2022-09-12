import requests
import simplejson
from django.core.management import BaseCommand
from django.db.models import signals
from requests import HTTPError

from bims.models import (
    BiologicalCollectionRecord,
    collection_post_save_handler,
)
from bims.utils.logger import log


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--limit',
            dest='limit',
            default=None,
            help='Limit'
        )

    def handle(self, *args, **options):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        limit = options.get('limit', None)
        occurrences = BiologicalCollectionRecord.objects.filter(
            additional_data__datasetKey__isnull=True,
            source_collection='gbif',
        ).exclude(upstream_id='')
        log('Total gbif occurrences to update : {}'.format(
            occurrences.count()))

        api_url = 'https://api.gbif.org/v1/occurrence/'
        index = 1
        total = occurrences.count()

        if limit:
            occurrences = occurrences[:int(limit)]
            total = limit

        for occurrence in occurrences:
            log(f'{occurrence.uuid} - {index}/{total}')
            index += 1
            try:
                response = requests.get(api_url + occurrence.upstream_id)
                json_result = response.json()
            except (HTTPError, simplejson.errors.JSONDecodeError) as e:
                log('Error -- skip')
                occurrence.delete()
                continue
            additional_data = dict(occurrence.additional_data, **json_result)
            occurrence.additional_data = additional_data
            occurrence.save()

        signals.post_save.connect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
