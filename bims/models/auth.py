import traceback
import logging

from django.contrib.auth.signals import user_logged_out
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.dispatch import receiver
from allauth.account.signals import user_signed_up

from geonode.decorators import on_ogc_backend
from geonode.base.auth import (delete_old_tokens,
                               remove_session_token)

from preferences import preferences


logger = logging.getLogger(__name__)


@receiver(user_signed_up, dispatch_uid="user_signed_up")
def user_signed_up_(request, user, **kwargs):
    from geonode.people.models import Profile
    user_email = user.email

    # Try to change the username
    new_username = '{first_name}_{last_name}'.format(
        first_name=user.first_name.lower(),
        last_name=user.last_name.lower()
    )

    if not Profile.objects.filter(username=new_username).exists():
        user.username = new_username
        user.save()

    username = user.username

    try:
        site = Site.objects.first()
        bims_site_name = site.name
    except Site.DoesNotExist:
        bims_site_name = 'Biodiversity Information System'

    bims_team_name = preferences.SiteSetting.default_site_name
    if not bims_team_name:
        bims_team_name = 'BIMS'

    data = {
        'site': bims_site_name,
        'username': username,
        'team_name': bims_team_name,
        'bims_email': settings.SERVER_EMAIL
    }

    send_mail(
        '{} Registration Confirmation'.format(bims_site_name),
        'Welcome,\n\n'
        'Thank you for registering the {site}\n\n'
        'Your username is {username}\n\n'
        'You will receive an email as soon as you account has been activated.'
        '\n\n'
        'Please do not hesitate to contact us by emailing {bims_email} '
        'should you have any questions.\n\n'
        'Regards,\n'
        '{team_name} Team'.format(**data),
        settings.SERVER_EMAIL,
        [user_email],
        fail_silently=False
    )
