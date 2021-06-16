# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Permission
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from geonode.people.models import Profile

from bims.models import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord


class SendNotificationValidation(LoginRequiredMixin, APIView):

    def get(self, request):
        site = request.get_host()
        scheme = request.scheme
        pk = request.GET.get('pk', None)
        model = request.GET.get('model', None)
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
                    bio_record = BiologicalCollectionRecord.objects.get(pk=pk)

                    try:
                        taxon_classname = bio_record.taxonomy.class_name
                        class_permission = Permission.objects.filter(
                            content_type__app_label='bims',
                            codename='can_validate_%s' % taxon_classname.lower()
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
                    bio_record.ready_for_validation = True
                    bio_record.save()
                    send_mail(
                        '[BIMS] Record is ready to be validated',
                        'Dear Validator,\n\n'
                        'The following object is ready to be reviewed:\n'
                        '{}://{}/nonvalidated-list/?pk={}\n\n'
                        'Sincerely,\nBIMS Team.'.format(scheme, site, pk),
                        '{}'.format(settings.SERVER_EMAIL),
                        validator_emails,
                        fail_silently=False
                    )
                    return JsonResponse({'status': 'success'})
                except BiologicalCollectionRecord.DoesNotExist:
                    return HttpResponse(
                        'Object Does Not Exist',
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                try:
                    new_site = LocationSite.objects.get(pk=pk)
                except LocationSite.DoesNotExist:
                    return HttpResponse(
                        'Site Does Not Exist',
                        status=status.HTTP_400_BAD_REQUEST
                    )

                send_mail(
                    '[BIMS] New site is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following site is ready to be reviewed:\n'
                    '{}://{}/nonvalidated-site/?pk={}\n\n'
                    'Sincerely,\nBIMS Team.'.format(scheme, site, new_site.pk),
                    '{}'.format(settings.SERVER_EMAIL),
                    validator_emails,
                    fail_silently=False
                )
                return JsonResponse({'status': 'success'})

        else:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
