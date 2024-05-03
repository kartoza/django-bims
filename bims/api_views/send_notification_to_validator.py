# coding=utf-8
from braces.views import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import status

from bims.models import LocationSite
from bims.models.survey import Survey
from bims.models.notification import (
    get_recipients_for_notification,
    SITE_VISIT_VALIDATION,
    SITE_VALIDATION
)
from bims.tasks.send_notification import send_mail_notification
from bims.utils.domain import get_current_domain


def send_notification_validation(pk, model=None, request=None):
    site = get_current_domain()
    validator_emails = get_recipients_for_notification(
        SITE_VISIT_VALIDATION
    )
    if pk is not None:
        if model is None:
            try:
                site_visit = Survey.objects.get(pk=pk)

                site_visit.ready_for_validation = True
                site_visit.save()

                if request:
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        'Validation notification is sent.',
                        'site_visit_validation'
                    )

                if site_visit.sass_site_visit:
                    site_visit_detail_url = (
                        '{}/sass/view/{}/'.format(
                            site, site_visit.sass_site_visit.id
                        )
                    )
                else:
                    site_visit_detail_url = (
                        '{}/site-visit/detail/{}/'.format(
                            site, pk
                        )
                    )

                site_visit_list_url = (
                    '{}/site-visit/list/?&inReview=True'.format(
                        site
                    )
                )

                send_mail_notification.delay(
                    'Site visit is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following site visit is ready to be reviewed:\n'
                    '{}\n\n'
                    'Go to the following link to validate the data:\n'
                    '{}\n\n'
                    'Sincerely,\nBIMS Team.'.format(
                        site_visit_detail_url,
                        site_visit_list_url
                    ),
                    '{}'.format(settings.SERVER_EMAIL),
                    validator_emails
                )
                return JsonResponse({'status': 'success'})
            except Survey.DoesNotExist:
                return HttpResponse(
                    'Object Does Not Exist',
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            try:
                new_site = LocationSite.objects.get(pk=pk)

                validator_emails = get_recipients_for_notification(
                    SITE_VALIDATION
                )

                new_site.ready_for_validation = True
                new_site.save()

                send_mail_notification.delay(
                    'New site is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following site is ready to be reviewed:\n'
                    '{}/nonvalidated-site/?pk={}\n\n'
                    'Sincerely,\nBIMS Team.'.format(site, new_site.pk),
                    '{}'.format(settings.SERVER_EMAIL),
                    validator_emails
                )
                return JsonResponse({'status': 'success'})

            except LocationSite.DoesNotExist:
                return HttpResponse(
                    'Site Does Not Exist',
                    status=status.HTTP_400_BAD_REQUEST
                )
    else:
        return HttpResponse(
            'Object Does Not Exist',
            status=status.HTTP_400_BAD_REQUEST
        )


class SendNotificationValidation(LoginRequiredMixin, APIView):

    def get(self, request):
        pk = request.GET.get('pk', None)
        model = request.GET.get('model', None)
        return send_notification_validation(
            pk,
            model,
            request
        )
