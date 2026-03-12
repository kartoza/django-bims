# coding=utf-8
from hashlib import sha256
import json
import os
import errno
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.db import connection
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.tasks.collection_record import download_collection_record_task
from bims.tasks.email_csv import send_csv_via_email
from bims.models.notification import (
    get_recipients_for_notification, DOWNLOAD_REQUEST
)
from bims.utils.domain import get_current_domain
from bims.tasks.send_notification import send_mail_notification

STALE_THRESHOLD_MINUTES = 10


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
        from bims.models.download_request import DownloadRequest
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

        try:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
        except DownloadRequest.DoesNotExist:
            return Response({
                'status': 'failed',
                'message': 'Download request does not exist'
            })

        # Persist the path and params so the resume task can restart the download
        params_dict = dict(self.request.GET)
        # Flatten single-value lists (QueryDict stores all values as lists)
        params_dict = {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                       for k, v in params_dict.items()}
        needs_save = False
        if download_request.download_path != path_file:
            download_request.download_path = path_file
            needs_save = True
        if download_request.download_params != params_dict:
            download_request.download_params = params_dict
            needs_save = True
        if needs_save:
            download_request.save(update_fields=['download_path', 'download_params'])

        if download_request.request_file and os.path.exists(
                str(download_request.request_file)):
            # Already completed - send via email again
            send_csv_via_email.delay(
                user_id=request.user.id,
                csv_file=str(download_request.request_file),
                download_request_id=download_request_id
            )
            return Response({
                'status': 'processing',
                'filename': filename
            })

        file_exists = os.path.exists(path_file)
        is_stale = False
        if file_exists and download_request.progress_updated_at:
            stale_cutoff = timezone.now() - timedelta(minutes=STALE_THRESHOLD_MINUTES)
            is_stale = download_request.progress_updated_at < stale_cutoff

        if file_exists and not is_stale:
            # Already in progress – do not start a duplicate task
            return Response({
                'status': 'processing',
                'filename': filename
            })

        if is_stale:
            # Delete any partial file so the task starts clean
            try:
                os.remove(path_file)
            except OSError:
                pass
            download_request.progress = None
            download_request.progress_updated_at = None
            download_request.save(update_fields=['progress', 'progress_updated_at'])

        if not file_exists or is_stale:
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


def send_new_csv_notification(user, date_request, approval_needed=True):
    """
    Send an email notify admin/staff that new request has been created
    :param user: User object
    :param date_request: Date of request
    :return:
    """
    email_template = 'csv_download/csv_new'
    recipients = get_recipients_for_notification(
        DOWNLOAD_REQUEST
    )
    ctx = {
        'username': user.username,
        'current_site': get_current_domain(),
        'date_request': date_request
    }
    subject = render_to_string(
        '{0}_subject.txt'.format(email_template),
        ctx
    ).strip()
    if not approval_needed:
        message = render_to_string(
            '{}_message_without_approval.txt'.format(email_template),
            ctx
        ).strip()
    else:
        message = render_to_string(
            '{}_message.txt'.format(email_template),
            ctx
        ).strip()

    send_mail_notification.delay(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients
    )


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
        'current_site': get_current_domain(),
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
