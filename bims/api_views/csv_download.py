# coding=utf-8
from hashlib import sha256
import json
import os
import errno
import zipfile
from datetime import datetime, date
from django.conf import settings
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from preferences import preferences
from bims.tasks.collection_record import download_collection_record_task
from bims.tasks.email_csv import send_csv_via_email as send_csv_via_email_task


class CsvDownload(APIView):
    """API to make csv download requests via email."""

    def get_hashed_name(self, request):
        query_string = json.dumps(
            request.GET.dict()
        ) + datetime.today().strftime('%Y%m%d')
        return sha256(
            query_string.encode('utf-8')
        ).hexdigest()

    def get(self, request, *args):
        # User need to be logged in before requesting csv download
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Not logged in')

        # Check if the file exists in the processed directory
        filename = self.get_hashed_name(request)
        folder = settings.PROCESSED_CSV_PATH
        download_request_id = self.request.GET.get('downloadRequestId', '')

        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, folder)):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, folder))

        path_folder = os.path.join(
            settings.MEDIA_ROOT,
            folder,
            request.user.username
        )

        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        path_file = os.path.join(path_folder, filename)
        if os.path.exists(path_file):
            os.remove(path_file)

        download_collection_record_task(
            path_file,
            self.request.GET,
            send_email=True,
            user_id=self.request.user.id
        )

        # if os.path.exists(path_file):
        #     send_csv_via_email_task.delay(
        #         user_id=request.user.id,
        #         csv_file=path_file,
        #         download_request_id=download_request_id
        #     )
        # else:
        #     download_collection_record_task.delay(
        #         path_file,
        #         self.request.GET,
        #         send_email=True,
        #         user_id=self.request.user.id
        #     )

        return Response({
            'status': 'processing',
            'filename': filename
        })


def send_new_csv_notification(user, date_request):
    """
    Send an email notify admin/staff that new request has been created
    :param user: User object
    :param date_request: Date of request
    :return:
    """
    email_template = 'csv_download/csv_new'
    staffs = get_user_model().objects.filter(is_superuser=True)
    ctx = {
        'username': user.username,
        'current_site': Site.objects.get_current(),
        'date_request': date_request
    }
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    )
    message = render_to_string(
        '{}_message.txt'.format(email_template),
        ctx
    )
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(staffs.values_list('email', flat=True)))
    msg.content_subtype = 'html'
    msg.send()


def send_rejection_csv(user, rejection_message = ''):
    """
    Send an email notify user that the request has been declined
    :param user: User object
    :param rejection_message: Message of the rejection
    :return:
    """
    email_template = 'csv_download/csv_rejected'
    ctx = {
        'username': user.username,
        'current_site': Site.objects.get_current(),
        'rejection_message': rejection_message
    }
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    )
    message = render_to_string(
        '{}_message.txt'.format(email_template),
        ctx
    )
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email])
    msg.content_subtype = 'html'
    msg.send()


def send_csv_via_email(
        user, csv_file, file_name = 'OccurrenceData',
        approved=False,
        download_request_id=None):
    """
    Send an email to requesting user with csv file attached
    :param user: User object
    :param csv_file: Path of csv file
    :param file_name: Name of the file
    :param approved: Whether the request has been approved or not
    :param download_request_id: Id of the download request
    :return:
    """
    from bims.models.download_request import DownloadRequest
    if not approved:
        if preferences.SiteSetting.enable_download_request_approval:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
            download_request.request_category = file_name
            download_request.request_file = csv_file
            download_request.save()
            return
        else:
            pass

    email_template = 'csv_download/csv_created'
    ctx = {
        'username': user.username,
        'current_site': Site.objects.get_current(),
    }
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    )
    message = render_to_string(
        '{}_message.txt'.format(email_template),
        ctx
    )
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email])
    zip_folder = os.path.join(
        settings.MEDIA_ROOT, settings.PROCESSED_CSV_PATH, user.username)
    if not os.path.exists(zip_folder):
        os.mkdir(zip_folder)
    zip_file = os.path.join(zip_folder, '{}.zip'.format(file_name))
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_file, '{}.csv'.format(file_name))
        if preferences.SiteSetting.readme_download:
            zf.write(
                preferences.SiteSetting.readme_download.path,
                os.path.basename(preferences.SiteSetting.readme_download.path)
            )
    msg.attach_file(zip_file, 'application/octet-stream')
    msg.content_subtype = 'html'
    msg.send()
