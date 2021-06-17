# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Permission
from django.conf import settings
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import status
from geonode.people.models import Profile
from bims.models.survey import Survey


class SendNotificationValidation(LoginRequiredMixin, APIView):

    def get(self, request):
        site = request.get_host()
        scheme = request.scheme
        pk = request.GET.get('pk', None)
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

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Validation notification is sent.',
                    'site_visit_validation'
                )

                send_mail(
                    'Site visit is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following site visit is ready to be reviewed:\n'
                    '{}://{}/site-visit/detail/{}/\n\n'
                    'Sincerely,\nBIMS Team.'.format(scheme, site, pk),
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
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
