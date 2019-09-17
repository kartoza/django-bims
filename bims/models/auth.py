import traceback
import urllib
import urllib2
import logging

from django.contrib.auth.signals import user_logged_out
from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver
from allauth.account.signals import user_signed_up

from geonode.decorators import on_ogc_backend
from geonode import geoserver
from oauth2_provider.models import AccessToken, get_application_model


logger = logging.getLogger(__name__)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def do_logout(sender, user, request, **kwargs):
    """
    Take action on user logout. Cleanup user access_token and send logout
    request to GeoServer
    """
    if 'access_token' in request.session:
        try:
            Application = get_application_model()
            app = Application.objects.get(name="GeoServer")

            # Lets delete the old one
            try:
                old = AccessToken.objects.get(user=user, application=app)
            except BaseException:
                pass
            else:
                old.delete()
        except BaseException:
            pass

        # Do GeoServer Logout
        if 'access_token' in request.session:
            access_token = request.session['access_token']
        else:
            access_token = None

        if access_token:
            url = "%s%s?access_token=%s" % (
                settings.OGC_SERVER['default']['LOCATION'],
                settings.OGC_SERVER['default']['LOGOUT_ENDPOINT'],
                access_token)
            header_params = {
                "Authorization": ("Bearer %s" % access_token)
            }
        else:
            url = "%s%s" % (settings.OGC_SERVER['default']['LOCATION'],
                            settings.OGC_SERVER['default']['LOGOUT_ENDPOINT'])
            header_params = {}

        param = {}
        data = urllib.urlencode(param)

        cookies = None
        for cook in request.COOKIES:
            name = str(cook)
            value = request.COOKIES.get(name)
            if name == 'csrftoken':
                header_params['X-CSRFToken'] = value

            cook = "%s=%s" % (name, value)
            if not cookies:
                cookies = cook
            else:
                cookies = cookies + '; ' + cook

        if cookies:
            if 'JSESSIONID' in request.session and \
                request.session['JSESSIONID']:
                cookies = cookies + '; JSESSIONID=' + \
                    request.session['JSESSIONID']
            header_params['Cookie'] = cookies

        gs_request = urllib2.Request(url, data, header_params)

        try:
            urllib2.urlopen(gs_request)
        except BaseException:
            tb = traceback.format_exc()
            if tb:
                logger.debug(tb)

        if 'access_token' in request.session:
            del request.session['access_token']

        request.session.modified = True


user_logged_out.connect(do_logout)


@receiver(user_signed_up, dispatch_uid="user_signed_up")
def user_signed_up_(request, user, **kwargs):
    username = request.POST.get('username')
    password = request.POST.get('password1')
    user_email = request.POST.get('email')
    try:
        bims_site_name = settings.BIMS_SITE_NAME
    except AttributeError:
        bims_site_name = 'Biodiversity Information System'

    try:
        bims_team_name = settings.BIMS_TEAM_NAME
    except AttributeError:
        bims_team_name = 'BIMS'

    try:
        bims_email = settings.BIMS_EMAIL_ADMIN
    except AttributeError:
        bims_email = 'admin@kartoza.com'

    data = {
        'site': bims_site_name,
        'username': username,
        'password': password,
        'team_name': bims_team_name,
        'bims_email': bims_email
    }

    send_mail(
        '{} Registration Confirmation'.format(bims_site_name),
        'Welcome,\n\n'
        'Thank you for registering the {site}\n\n'
        'Your username is {username}\n'
        'Your password is {password}\n\n'
        'You will receive an email as soon as you account has been activated.'
        '\n\n'
        'Please do not hesitate to contact us by emailing {bims_email} '
        'should you have any questions.\n\n'
        'Regards,\n'
        '{team_name} Team'.format(**data),
        bims_email,
        [user_email],
        fail_silently=False
    )
