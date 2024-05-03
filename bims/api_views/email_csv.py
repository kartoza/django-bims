from django.contrib.sites.models import Site
from django.db import connection
from django.http import JsonResponse
from rest_framework.views import APIView

from bims.tasks.send_notification import send_mail_notification


class TestSendEmail(APIView):

    def get(self, request):
        send_mail_notification.delay(
            subject=f'Testing Email 2',
            body=f'Testing 2',
            from_email='noreply@noreply.kartoza.com',
            recipient_list=['dimas@kartoza.com']
        )
        return JsonResponse({
            'status': '-',
            'message': ''
        })
