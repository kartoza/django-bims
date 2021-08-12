# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import status
from geonode.people.models import Profile

from bims.models import LocationSite
from bims.models.survey import Survey


def send_notification_validation(pk, model = None, request = None):
    site = Site.objects.get_current().domain
    permission = (
        Permission.objects.filter(
            content_type__app_label='bims', codename='can_validate_data')
    )
    validators = (
        Profile.objects.filter(
            Q(user_permissions__in=permission) |
            Q(groups__permissions__in=permission)
        ).distinct().values_list('email', flat=True)
    )
    superusers = (
        Profile.objects.filter(
            is_superuser=True
        ).values_list('email', flat=True)
    )
    validator_emails = list(superusers)
    if validators:
        validator_emails += list(validators)

    if pk is not None:
        if model is None:
            try:
                site_visit = Survey.objects.get(pk=pk)

                try:
                    class_permission = Permission.objects.filter(
                        content_type__app_label='bims',
                        codename='can_validate_site_visit'
                    )
                    class_validators = (
                        Profile.objects.filter(
                            Q(user_permissions__in=class_permission) |
                            Q(groups__permissions__in=class_permission)
                        ).values_list('email', flat=True)
                    )
                    validator_emails += list(class_validators)
                except AttributeError:
                    pass

                validator_emails = filter(None, validator_emails)
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

                send_mail(
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
                    validator_emails,
                    fail_silently=False
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

                try:
                    class_permission = Permission.objects.filter(
                        content_type__app_label='bims',
                        codename='can_validate_site'
                    )
                    class_validators = (
                        Profile.objects.filter(
                            Q(user_permissions__in=class_permission) |
                            Q(groups__permissions__in=class_permission)
                        ).values_list('email', flat=True)
                    )
                    validator_emails += list(class_validators)

                except AttributeError:
                    pass

                new_site.ready_for_validation = True
                new_site.save()

                send_mail(
                    'New site is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following site is ready to be reviewed:\n'
                    '{}/nonvalidated-site/?pk={}\n\n'
                    'Sincerely,\nBIMS Team.'.format(site, new_site.pk),
                    '{}'.format(settings.SERVER_EMAIL),
                    validator_emails,
                    fail_silently=False
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
