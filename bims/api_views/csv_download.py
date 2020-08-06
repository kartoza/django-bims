# coding=utf-8
import os
import errno
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

    def get(self, request, *args):
        # User need to be logged in before requesting csv download
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Not logged in')

        # What to do here
        email = request.user.email
        username = request.user.username

        # Check if the file exists in the processed directory
        filename = '{email}-{username}.csv'.format(
            email=email,
            username=username
        )
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
            os.remove(path_file)

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
    attachment = open(csv_file, 'rb')
    msg.attach('OccurrenceData.csv', attachment.read(), 'text/csv')
    msg.content_subtype = 'html'
    msg.send()
