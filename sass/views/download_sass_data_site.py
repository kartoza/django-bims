# coding=utf-8
import os
import errno
from hashlib import md5
import datetime
from django.http.response import JsonResponse
from django.conf import settings
from bims.models.location_site import LocationSite
from sass.models.site_visit import SiteVisit
from sass.tasks.download_sass_data_site import download_sass_data_site_task

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


def download_sass_data_site(request, **kwargs):
    """
    Download all sass data by site id
    """
    site_id = kwargs.get('site_id', None)
    try:
        site = LocationSite.objects.get(id=site_id)
    except LocationSite.DoesNotExist:
        response_message = 'Location Site does not exist'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Get SASS data
    site_visits = SiteVisit.objects.filter(
        location_site=site
    )
    if not site_visits:
        response_message = 'No SASS data for this site'
        return JsonResponse(get_response(FAILED_STATUS, response_message))

    # Filename
    search_uri = request.build_absolute_uri()
    today_date = datetime.date.today()
    date_data = today_date.isocalendar()[1] + today_date.year
    filename = md5(
        '%s%s%s' % (
            search_uri,
            len(site_visits),
            date_data)
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
    if os.path.exists(path_file):
        return JsonResponse(get_response(SUCCESS_STATUS, filename))

    download_sass_data_site_task.delay(
        filename,
        site_id,
        path_file
    )

    return JsonResponse(get_response(PROCESSING_STATUS, filename))
