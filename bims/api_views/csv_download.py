# coding=utf-8
from hashlib import sha256
import json
import os
import errno
import zipfile
from datetime import datetime
from django.conf import settings
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.tasks.collection_record import download_data_to_csv


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
        folder = 'csv_processed'
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
            send_csv_via_email(
                user=request.user,
                csv_file=path_file
            )
        else:
            download_data_to_csv.delay(
                path_file,
                self.request.GET,
                send_email=True,
                user_id=self.request.user.id
            )

        return Response({
            'status': 'processing',
            'filename': filename
        })


def send_csv_via_email(user, csv_file):
    """
    Send an email to requesting user with csv file attached
    :param user: User object
    :param csv_file: Path of csv file
    :return:
    """
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
        settings.MEDIA_ROOT, 'csv_processed', user.username)
    if not os.path.exists(zip_folder):
        os.mkdir(zip_folder)
    zip_file = os.path.join(zip_folder, 'OccurrenceData.zip')
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_file, 'OccurrenceData.csv')
    msg.attach_file(zip_file, 'application/octet-stream')
    msg.content_subtype = 'html'
    msg.send()
