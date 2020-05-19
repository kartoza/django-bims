import re
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from geonode.people.adapters import LocalAccountAdapter
from bims.models import Profile


class AccountAdapter(LocalAccountAdapter):

    def get_login_redirect_url(self, request):
        map_path = reverse('map-page')
        return map_path

    def clean_password(self, password, user=None):
        if re.match(r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{6,}$',
                    password):
            return password
        else:
            raise ValidationError('Password Error')

    def respond_user_inactive(self, request, user):
        # Sent email to superuser
        staffs = get_user_model().objects.filter(is_superuser=True)
        try:
            current_site = Site.objects.get_current()
            profile = Profile.objects.get(user=user)
            ctx = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'organization': user.organization,
                'user_id': user.id,
                'current_site': current_site,
                'site_name': current_site.name,
                'email': user.email,
                'role': profile.get_role_display(),
                'inviter': user,
            }
            email_template = 'pinax/notifications/account_created'
            subject = render_to_string(
                '{0}_subject.txt'.format(email_template),
                ctx
            )
            email_body = render_to_string(
                '{0}_message.txt'.format(email_template),
                ctx
            )
            msg = EmailMultiAlternatives(
                subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                list(staffs.values_list('email', flat=True)))
            msg.send()

        except BaseException:
            import traceback
            traceback.print_exc()
        return HttpResponseRedirect(
            reverse("moderator_contacted", kwargs={"inactive_user": user.id})
        )
