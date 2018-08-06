# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Group
from rest_framework.views import APIView
from rest_framework import status
from geonode.people.models import Profile


class SendNotificationValidation(LoginRequiredMixin, APIView):

    def get(self, request):
        site = request.get_host()
        scheme = request.scheme
        pk = request.GET.get('pk', None)
        group = Group.objects.get(name='validator')
        validators = Profile.objects.filter(groups=group)
        validator_emails = []
        for validator in validators:
            validator_emails.append(validator.email)

        if pk is not None:
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
        else:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
