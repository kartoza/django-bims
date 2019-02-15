# coding=utf-8
import csv
import logging
from celery import shared_task
from sass.models import SiteVisit, SiteVisitTaxon
from sass.serializers.sass_data_serializer import SassDataSerializer

logger = logging.getLogger('bims')


@shared_task(name='sass.tasks.download_sass_data_site', queue='update')
def download_sass_data_site_task(filename, site_id, path_file):
    from bims.utils.celery import memcache_lock

    lock_id = '{0}-lock-{1}'.format(
        filename,
        site_id
    )
    oid = '{0}'.format(filename)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            site_visits = SiteVisit.objects.filter(location_site_id=site_id)
            site_visit_taxon = SiteVisitTaxon.objects.filter(
                site_visit__in=site_visits
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
