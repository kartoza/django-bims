# coding=utf-8
import os
import errno
from hashlib import sha256
import datetime
from django.http.response import JsonResponse
from django.conf import settings
from bims.api_views.search import CollectionSearch
from sass.models.site_visit_taxon import SiteVisitTaxon
from sass.tasks.download_sass_data_site import (
    download_sass_data_site_task,
    download_sass_summary_data_task
)
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.api_views.csv_download import send_csv_via_email


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
    filename = sha256(
        str('%s%s%s' % (
            uri,
            additional_parameter,
            today_date)).encode('utf-8')
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
    search = CollectionSearch(filters)
    collection_records = search.process_search()
    csv_name = request.GET.get('csvName', 'SASS-Data')

    # Get SASS data
    site_visit_taxa = SiteVisitTaxon.objects.filter(
        id__in=list(collection_records.values_list('id', flat=True)),
        taxonomy__taxongroup__category=(
            TaxonomicGroupCategory.SASS_TAXON_GROUP.name
        )
    )
    if not site_visit_taxa:
        response_message = 'No SASS data for this site'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Filename
    search_uri = request.build_absolute_uri()
    path_file, filename = get_filename(search_uri, site_visit_taxa.count())

    if os.path.exists(path_file):
        send_csv_via_email(
            user=request.user,
            csv_file=path_file,
            file_name=csv_name
        )
        return JsonResponse(get_response(SUCCESS_STATUS, filename))

    download_sass_data_site_task.delay(
        filename,
        filters,
        path_file,
        user_id=request.user.id,
        send_email=True
    )

    return JsonResponse(get_response(PROCESSING_STATUS, filename))


def download_sass_summary_data(request):
    """
    Download sass data summary
    """
    filters = request.GET
    search = CollectionSearch(filters)
    collection_records = search.process_search()
    csv_name = request.GET.get('csvName', 'SASS-Summary')

    # Get SASS data
    site_visit_taxa = SiteVisitTaxon.objects.filter(
        id__in=list(collection_records.values_list('id', flat=True)),
        taxonomy__taxongroup__category=(
            TaxonomicGroupCategory.SASS_TAXON_GROUP.name
        )
    )
    if not site_visit_taxa:
        response_message = 'No SASS data for this site'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Filename
    search_uri = request.build_absolute_uri()
    path_file, filename = get_filename(search_uri, site_visit_taxa.count())

    if os.path.exists(path_file):
        send_csv_via_email(
            user=request.user,
            csv_file=path_file,
            file_name=csv_name
        )
        return JsonResponse(get_response(SUCCESS_STATUS, filename))

    download_sass_summary_data_task.delay(
        filename,
        filters,
        path_file,
        user_id=request.user.id,
        send_email=True
    )

    return JsonResponse(get_response(PROCESSING_STATUS, filename))
