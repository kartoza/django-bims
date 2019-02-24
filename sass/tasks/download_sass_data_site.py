# coding=utf-8
import csv
import logging
from celery import shared_task
from bims.api_views.search_version_2 import SearchVersion2
from sass.models import SiteVisitTaxon
from sass.serializers.sass_data_serializer import SassDataSerializer

logger = logging.getLogger('bims')


@shared_task(name='sass.tasks.download_sass_data_site', queue='update')
def download_sass_data_site_task(filename, filters, path_file):
    from bims.utils.celery import memcache_lock

    lock_id = '{0}-lock-{1}'.format(
        filename,
        len(filters)
    )
    oid = '{0}'.format(filename)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search = SearchVersion2(filters)
            collection_records = search.process_search()
            site_visit_taxon = SiteVisitTaxon.objects.filter(
                id__in=collection_records
            ).order_by('site_visit__site_visit_date')
            serializer = SassDataSerializer(
                site_visit_taxon,
                many=True,
            )
            headers = serializer.data[0].keys()
            rows = serializer.data
            with open(path_file, 'wb') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            return
    logger.info(
        'Csv %s is already being processed by another worker',
        filename)
