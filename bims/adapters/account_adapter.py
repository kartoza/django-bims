import re
import requests
import json

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.account.utils import user_email
from allauth.account.utils import user_username

from bims.utils.domain import get_current_domain
from geonode.groups.models import GroupProfile
from invitations.adapters import BaseInvitationsAdapter
from preferences import preferences
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from bims.models import Profile
from bims.models.notification import (
    get_recipients_for_notification,
    ACCOUNT_CREATED
)


class LocalAccountAdapter(DefaultAccountAdapter, BaseInvitationsAdapter):
    """Customizations for local accounts

    Check `django-allauth's documentation`_ for more details on this class.

    .. _django-allauth's documentation:
       http://django-allauth.readthedocs.io/en/latest/advanced.html#creating-and-populating-user-instances

    """

    def is_open_for_signup(self, request):
        return _site_allows_signup(request)

    def get_login_redirect_url(self, request):
        profile_path = reverse(
            "profile_detail", kwargs={"username": request.user.username})
        return profile_path

    def populate_username(self, request, user):
        # validate the already generated username with django validation
        # if it passes use that, otherwise use django-allauth's way of
        # generating a unique username
        try:
            user.full_clean()
            safe_username = user_username(user)
        except ValidationError:
            safe_username = self.generate_unique_username([
                user_field(user, 'first_name'),
                user_field(user, 'last_name'),
                user_email(user),
                user_username(user)
            ])
        user_username(user, safe_username)

    def send_invitation_email(self, email_template, email, context):
        enh_context = self.enhanced_invitation_context(context)
        self.send_mail(email_template, email, enh_context)

    def enhanced_invitation_context(self, context):
        user = context.get("inviter") if context.get("inviter") else context.get("user")
        full_name = " ".join((user.first_name, user.last_name)) if user.first_name or user.last_name else None
        user_groups = GroupProfile.objects.filter(
            slug__in=user.groupmember_set.all().values_list("group__slug", flat=True))
        enhanced_context = context.copy()
        enhanced_context.update({
            "username": user.username,
            "inviter_name": full_name or str(user),
            "inviter_first_name": user.first_name or str(user),
            "inviter_id": user.id,
            "groups": user_groups,
            "MEDIA_URL": settings.MEDIA_URL,
            "SITEURL": settings.SITEURL,
            "STATIC_URL": settings.STATIC_URL
        })
        return enhanced_context

    def save_user(self, request, user, form, commit=True):
        user = super(LocalAccountAdapter, self).save_user(
            request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def respond_user_inactive(self, request, user):
        return _respond_inactive_user(user)


class AccountAdapter(LocalAccountAdapter):

    def _verify_recaptcha(self, token):
        url = 'https://www.google.com/recaptcha/api/siteverify'
        post_data = {
            'secret': preferences.SiteSetting.recaptcha_secret_key,
            'response': token
        }
        response = requests.post(url, data = post_data)
        response_obj = json.loads(response.text)
        if not response_obj['success']:
            raise ValidationError('Sign up failed!')

    def save_user(self, request, user, form, commit=True):
        recaptcha_token = request.POST.get('recaptcha_token', None)
        if not recaptcha_token:
            raise ValidationError('Sign up failed!')
        self._verify_recaptcha(recaptcha_token)
        user = super(LocalAccountAdapter, self).save_user(
            request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

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
        try:
            current_site = get_current_domain()
            profile = Profile.objects.get(user=user)
            ctx = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'organization': user.organization,
                'user_id': user.id,
                'current_site': current_site,
                'site_name': current_site,
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
                get_recipients_for_notification(ACCOUNT_CREATED)
            )
            msg.send()

        except BaseException:
            import traceback
            traceback.print_exc()
        return HttpResponseRedirect(
            reverse("moderator_contacted", kwargs={"inactive_user": user.id})
        )


def _site_allows_signup(django_request):
    if getattr(settings, "ACCOUNT_OPEN_SIGNUP", True):
        result = True
    else:
        try:
            result = bool(django_request.session.get("account_verified_email"))
        except AttributeError:
            result = False
    return result


def _respond_inactive_user(user):
    return HttpResponseRedirect(
        reverse("moderator_contacted", kwargs={"inactive_user": user.id})
    )
