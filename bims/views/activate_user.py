# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'

from django.contrib.auth.models import User
from django.shortcuts import reverse, render
from django.http import Http404, HttpResponseRedirect


def activate_user(request, **kwargs):
    username = kwargs.get('username', None)
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404('Sorry! This user does not exist.')

    if request.method == 'POST':
        new_password = request.POST.get('password1', '')
        user.set_password(new_password)
        user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse('landing-page'))

    return render(request, 'activate_user.html')
