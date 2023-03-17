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
from bims.tasks.email_csv import send_csv_via_email


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

        if os.path.exists(path_file):
            send_csv_via_email.delay(
                user_id=request.user.id,
                csv_file=path_file,
                download_request_id=download_request_id
            )
        else:
            download_collection_record_task.delay(
                path_file,
                self.request.GET,
                send_email=True,
                user_id=self.request.user.id
            )

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
