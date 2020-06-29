# coding=utf-8
import csv
import logging
from celery import shared_task
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Q, Value, CharField
)
from django.db.models.functions import Cast, Concat
from bims.api_views.search import Search
from sass.models import SiteVisitTaxon
from bims.models.location_context import LocationContext
from sass.serializers.sass_data_serializer import SassDataSerializer
from sass.serializers.sass_data_serializer import SassSummaryDataSerializer

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
            search = Search(filters)
            context = {
                'filters': filters
            }
            collection_records = search.process_search()
            site_visit_taxon = SiteVisitTaxon.objects.filter(
                id__in=collection_records
            ).order_by('site_visit__site_visit_date')
            serializer = SassDataSerializer(
                site_visit_taxon,
                many=True,
                context=context
            )
            headers = serializer.data[0].keys()
            rows = serializer.data

            formatted_headers = []
            # Rename headers
            for header in headers:
                formatted_headers.append(header.replace('_', ' ').capitalize())

            with open(path_file, 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
                writer.writeheader()
                writer.fieldnames = headers
                for row in rows:
                    try:
                        writer.writerow(row)
                    except ValueError:
                        writer.fieldnames = row.keys()
                        writer.writerow(row)
            return
    logger.info(
        'Csv %s is already being processed by another worker',
        filename)


@shared_task(name='sass.tasks.download_sass_summary_data', queue='update')
def download_sass_summary_data_task(filename, filters, path_file):
    from bims.utils.celery import memcache_lock
    import random

    lock_id = '{0}-lock-{1}'.format(
        filename,
        len(filters)
    )
    oid = random.randint(1, 101)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search = Search(filters)
            context = {
                'filters': filters
            }

            collection_records = search.process_search()
            collection_ids = list(
                collection_records.values_list('id', flat=True))
            # Get SASS data
            site_visit_taxa = SiteVisitTaxon.objects.filter(
                id__in=collection_ids
            )
            summary = site_visit_taxa.annotate(
                date=F('collection_date'),
            ).values('date').annotate(
                sampling_date=F('site_visit__site_visit_date'),
                full_name=Concat(
                    'site_visit__owner__first_name',
                    Value(' '),
                    'site_visit__owner__last_name',
                    output_field=CharField()
                )
            ).values('sampling_date', 'full_name').annotate(
                count=Count('sass_taxon'),
                sass_score=Sum(Case(
                    When(
                        condition=Q(site_visit__sass_version=5,
                                    sass_taxon__sass_5_score__isnull=False),
                        then='sass_taxon__sass_5_score'),
                    default='sass_taxon__score'
                )),
                sass_id=F('site_visit__id'),
                FBIS_site_code=Case(
                    When(site_visit__location_site__site_code__isnull=False,
                         then='site_visit__location_site__site_code'),
                    default='site_visit__location_site__name'
                ),
                site_id=F('site_visit__location_site__id'),
                sass_version=F('site_visit__sass_version'),
                site_description=F(
                    'site_visit__location_site__site_description'),
                river_name=Case(
                    When(site_visit__location_site__river__isnull=False,
                         then='site_visit__location_site__river__name'),
                    default=Value('-')
                ),
                latitude=F('site_visit__location_site__latitude'),
                longitude=F('site_visit__location_site__longitude'),
                source_reference=F('source_reference'),
                ecological_category=F('site_visit__'
                                      'sitevisitecologicalcondition__'
                                      'ecological_condition__category')
            ).annotate(
                aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                                FloatField()),
            ).order_by('sampling_date')
            context['location_contexts'] = LocationContext.objects.filter(
                site__in=site_visit_taxa.values('site_visit__location_site')
            )

            serializer = SassSummaryDataSerializer(
                summary,
                many=True,
                context=context
            )
            headers = serializer.data[0].keys()
            rows = serializer.data
            formatted_headers = []

            # Rename headers
            for header in headers:
                header_split = [
                    word[0].upper() + word[1:] for word in header.split('_')
                ]
                header = ' '.join(header_split)
                formatted_headers.append(header)

            with open(path_file, 'wb') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
                writer.writeheader()
                writer.fieldnames = headers
                for row in rows:
                    try:
                        writer.writerow(row)
                    except ValueError:
                        writer.fieldnames = row.keys()
                        writer.writerow(row)
            return
    logger.info(
        'Csv %s is already being processed by another worker',
        filename)
