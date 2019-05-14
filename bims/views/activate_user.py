# coding=utf-8
from django.shortcuts import reverse, render
from django.http import Http404, HttpResponseRedirect
from geonode.people.models import Profile


def activate_user(request, **kwargs):
    username = kwargs.get('username', None)
    try:
        user = Profile.objects.get(username=username)
    except Profile.DoesNotExist:
        raise Http404('Sorry! This user does not exist.')

    if request.method == 'POST':
        new_password = request.POST.get('password1', '')
        user.set_password(new_password)
        user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse('landing-page'))

    return render(request, 'activate_user.html')
