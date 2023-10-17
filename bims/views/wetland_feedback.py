from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.views import View
from braces.views import LoginRequiredMixin

from bims.models.notification import (
    get_recipients_for_notification,
    WETLAND_ISSUE_CREATED
)


class WetlandFeedbackView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):

        email_template = 'notifications/wetland_issue_created'
        issue = request.POST.get('issue', '')
        description = request.POST.get('description', '')
        issue_type = request.POST.get('issue_type', '')
        location = request.POST.get('location', '')

        if not location:
            raise Http404('Missing location')

        longitude = location.split(',')[0]
        latitude = location.split(',')[1]

        ctx = {
            'username': self.request.user.email,
            'current_site': Site.objects.get_current(),
            'issue': issue,
            'issue_type': issue_type,
            'description': description,
            'longitude': longitude,
            'latitude': latitude,
        }

        subject = render_to_string(
            '{0}_subject.txt'.format(email_template),
            ctx
        ).strip()
        message = render_to_string(
            '{}_message_admins.txt'.format(email_template),
            ctx
        )
        msg = EmailMultiAlternatives(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            get_recipients_for_notification(
                WETLAND_ISSUE_CREATED
            )
        )
        msg.send()

        return JsonResponse({
            'status': 'OK',
        })
