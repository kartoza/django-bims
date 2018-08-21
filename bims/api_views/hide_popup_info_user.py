# coding=utf-8
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from bims.models.profile import Profile as BimsProfile


class HidePopupInfoUser(LoginRequiredMixin, APIView):

    def get(self, request):
        try:
            object = BimsProfile.objects.get(user=self.request.user)
            object.hide_bims_info = True
            object.save()
            return JsonResponse({'status': 'success'})
        except BimsProfile.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
