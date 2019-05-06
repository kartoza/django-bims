# coding=utf-8
import os
import csv
import errno
from hashlib import md5
import datetime
from django.http.response import JsonResponse
from django.conf import settings
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Q, Value
)
from django.db.models.functions import Cast
from bims.api_views.search_version_2 import SearchVersion2
from sass.models.site_visit_taxon import SiteVisitTaxon
from sass.tasks.download_sass_data_site import download_sass_data_site_task
from sass.serializers.sass_data_serializer import SassSummaryDataSerializer

FAILED_STATUS = 'failed'
SUCCESS_STATUS = 'success'
PROCESSING_STATUS = 'processing'
RESPONSE_STATUS = 'status'
RESPONSE_MESSAGE = 'message'


def get_response(status, message):
    """
    Get dictionary response
    :param status: status of response
    :param message: message of response
    :return:
    """
    return {
        RESPONSE_STATUS: status,
        RESPONSE_MESSAGE: message
    }


def get_filename(uri, additional_parameter):
    """
    Create a filename with uri
    :param uri: request uri
    :param additional_parameter: additional parameter for filename
    :return: path_file, filename
    """
    today_date = datetime.date.today()
    filename = md5(
        '%s%s%s' % (
            uri,
            additional_parameter,
            today_date)
    ).hexdigest()
    filename += '.csv'

    # Check if filename exists
    folder = 'csv_processed'
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    path_file = os.path.join(path_folder, filename)
    try:
        os.mkdir(path_folder)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass

    return path_file, filename


def download_sass_data_site(request, **kwargs):
    """
    Download all sass data by site id
    """
    filters = request.GET
    search = SearchVersion2(filters)
    collection_records = search.process_search()
    # Get SASS data
    site_visit_taxa = SiteVisitTaxon.objects.filter(
        id__in=collection_records
    )
    if not site_visit_taxa:
        response_message = 'No SASS data for this site'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Filename
    search_uri = request.build_absolute_uri()
    path_file, filename = get_filename(search_uri, len(site_visit_taxa))

    if os.path.exists(path_file):
        return JsonResponse(get_response(SUCCESS_STATUS, filename))

    download_sass_data_site_task.delay(
        filename,
        filters,
        path_file
    )

    return JsonResponse(get_response(PROCESSING_STATUS, filename))


def download_sass_summary_data(request):
    """
    Download sass data summary
    """
    filters = request.GET
    search = SearchVersion2(filters)
    collection_records = search.process_search()

    # Get SASS data
    site_visit_taxa = SiteVisitTaxon.objects.filter(
        id__in=list(collection_records.values_list('id', flat=True))
    )
    summary = site_visit_taxa.annotate(
        sampling_date=F('site_visit__site_visit_date'),
    ).values('sampling_date').annotate(
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
        assessor=F('site_visit__assessor__username'),
        sass_version=F('site_visit__sass_version'),
        site_description=F('site_visit__location_site__site_description'),
        river_name=Case(
            When(site_visit__location_site__river__isnull=False,
                 then='site_visit__location_site__river__name'),
            default=Value('-')
        ),
        latitude=F('site_visit__location_site__latitude'),
        longitude=F('site_visit__location_site__longitude'),
        time_of_day=F('site_visit__time'),
        reference=F('reference'),
        reference_category=F('reference_category'),
    ).annotate(
        aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                        FloatField()),
    ).order_by('sampling_date')

    if not site_visit_taxa:
        response_message = 'No SASS data'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Filename
    search_uri = request.build_absolute_uri()
    path_file, filename = get_filename(search_uri, len(site_visit_taxa))

    serializer = SassSummaryDataSerializer(
        summary,
        many=True,
    )
    headers = serializer.data[0].keys()
    rows = serializer.data
    formatted_headers = []

    # Rename headers
    for header in headers:
        formatted_headers.append(header.replace('_', ' ').capitalize())

    with open(path_file, 'wb') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
        writer.writeheader()
        writer.fieldnames = headers
        for row in rows:
            writer.writerow(row)

    return JsonResponse(get_response(SUCCESS_STATUS, filename))
