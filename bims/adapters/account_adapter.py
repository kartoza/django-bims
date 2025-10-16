import re
import requests
import json

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field, user_email, user_username
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from tenants.models import Domain

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
from bims.models import Profile
from bims.models.notification import (
    get_recipients_for_notification,
    ACCOUNT_CREATED
)


class LocalAccountAdapter(DefaultAccountAdapter, BaseInvitationsAdapter):
    """
    Customizations for local accounts + TENANT-AWARE site/from email for allauth.
    Uses django-tenants Domain table as the source of truth for hostnames.
    """

    def _host_from_request_raw(self, request) -> str | None:
        if not request:
            return None
        host = (request.get_host() or "").strip().lower()
        return host or None

    def _hostname_only(self, host: str | None) -> str | None:
        if not host:
            return None
        return host.split(":")[0]

    def _domain_from_django_tenants(self, host: str | None) -> str | None:
        if not host:
            return None
        hostname = self._hostname_only(host)
        if not hostname:
            return None
        dom = Domain.objects.filter(domain=hostname).first()
        return dom.domain if dom else None

    def _tenant_host(self, request) -> str | None:
        raw = self._host_from_request_raw(request)
        from_tenants = self._domain_from_django_tenants(raw)
        return from_tenants or self._hostname_only(raw)

    def format_email_subject(self, subject):
        host = self._tenant_host(self.request)
        prefix = "[{name}] ".format(name=host)
        return prefix + force_str(subject)

    def is_open_for_signup(self, request):
        return _site_allows_signup(request)

    def get_login_redirect_url(self, request):
        profile_path = reverse("profile_detail", kwargs={"username": request.user.username})
        return profile_path

    def send_mail(self, template_prefix, email, context):
        ctx = {
            "email": email,
            "current_site": self._tenant_host(self.request),
        }
        ctx.update(context)
        msg = self.render_mail(template_prefix, email, ctx)
        msg.send()

    def populate_username(self, request, user):
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
        user = super(LocalAccountAdapter, self).save_user(request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def respond_user_inactive(self, request, user):
        return _respond_inactive_user(user)


class AccountAdapter(LocalAccountAdapter):
    """
    Extends LocalAccountAdapter with your reCAPTCHA and custom redirects.
    Inherits the tenant-aware behavior above.
    """

    def _verify_recaptcha(self, token):
        url = 'https://www.google.com/recaptcha/api/siteverify'
        post_data = {
            'secret': preferences.SiteSetting.recaptcha_secret_key,
            'response': token
        }
        response = requests.post(url, data=post_data, timeout=10)
        response_obj = json.loads(response.text)
        if not response_obj.get('success'):
            raise ValidationError('Sign up failed!')

    def save_user(self, request, user, form, commit=True):
        if not settings.DEBUG:
            recaptcha_token = request.POST.get('recaptcha_token', None)
            if not recaptcha_token:
                raise ValidationError('Sign up failed!')
            self._verify_recaptcha(recaptcha_token)
        user = super(LocalAccountAdapter, self).save_user(request, user, form, commit=commit)
        if settings.ACCOUNT_APPROVAL_REQUIRED:
            user.is_active = False
            user.save()
        return user

    def get_login_redirect_url(self, request):
        return reverse('map-page')

    def clean_password(self, password, user=None):
        if not password:
            raise ValidationError(_('Password cannot be empty.'))
        errors = []
        if len(password) < 12:
            errors.append(_('Must be at least 12 characters long.'))
        if not re.search(r'[A-Z]', password):
            errors.append(_('Must include at least one uppercase letter.'))
        if not re.search(r'[a-z]', password):
            errors.append(_('Must include at least one lowercase letter.'))
        if not re.search(r'\d', password):
            errors.append(_('Must include at least one number.'))
        if not re.search(r'[^A-Za-z0-9]', password):
            errors.append(_('Must include at least one symbol (e.g. !@#$).'))
        if user:
            lowered = password.lower()
            for attr in ('username', 'email', 'first_name', 'last_name'):
                val = getattr(user, attr, None)
                if val:
                    token = str(val).split('@')[0].lower()
                    if token and token in lowered:
                        errors.append(_('Cannot contain your name, username, or email.'))
                        break

        if errors:
            raise ValidationError(errors)

        return password

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
            subject = render_to_string(f'{email_template}_subject.txt', ctx)
            email_body = render_to_string(f'{email_template}_message.txt', ctx)
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
