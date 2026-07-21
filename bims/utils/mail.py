from django.contrib.auth import get_user_model
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.db import connection

from tenants.models import Domain


def get_domain_name() -> str:
    tenant = getattr(connection, "tenant", None)
    tenant_name = getattr(tenant, "name", "") or getattr(tenant, "schema_name", "") or ""
    dom = Domain.objects.filter(tenant__name=tenant_name).first()
    return dom.domain if dom else tenant_name


def mail_superusers(subject: str, body: str, attachment=None):
    """
    Email all superusers.

    :param attachment: Optional ``(filename, content, mimetype)`` tuple to
        attach to the message (e.g. a CSV report).
    """
    superusers = list(
        get_user_model()
        .objects.filter(is_superuser=True, email__isnull=False)
        .values_list("email", flat=True)
    )
    if not superusers:
        return

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if attachment:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=superusers,
        )
        email.attach(*attachment)
        email.send(fail_silently=True)
    else:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=superusers,
            fail_silently=True,
        )
