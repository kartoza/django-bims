# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Permission
from rest_framework.views import APIView
from rest_framework import status
from geonode.people.models import Profile
from bims.models.biological_collection_record import BiologicalCollectionRecord


class SendNotificationValidation(LoginRequiredMixin, APIView):

    def get(self, request):
        site = request.get_host()
        scheme = request.scheme
        pk = request.GET.get('pk', None)
        permission = Permission.objects.filter(content_type__app_label='bims', codename='can_validate_data')
        validators = \
            Profile.objects.filter(
                Q(user_permissions=permission) |
                Q(groups__permissions=permission)
            ).distinct()
        validator_emails = []
        for validator in validators:
            validator_emails.append(validator.email)

        if pk is not None:
            try:
                bio_record = BiologicalCollectionRecord.objects.get(pk=pk)
                bio_record.ready_for_validation = True
                bio_record.save()
                send_mail(
                    '[BIMS] Object is ready to be validated',
                    'Dear Validator,\n\n'
                    'The following object is ready to be reviewed:\n'
                    '{}://{}/nonvalidated-list/?pk={}\n\n'
                    'Sincerely,\nBIMS Team.'.format(scheme, site, pk),
                    '{}'.format(request.user.email),
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
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
