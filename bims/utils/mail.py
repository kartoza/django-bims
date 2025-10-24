from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection

from tenants.models import Domain


def get_domain_name() -> str:
    tenant = getattr(connection, "tenant", None)
    tenant_name = getattr(tenant, "name", "") or getattr(tenant, "schema_name", "") or ""
    dom = Domain.objects.filter(tenant__name=tenant_name).first()
    return dom.domain if dom else tenant_name


def mail_superusers(subject: str, body: str):
    superusers = (
        get_user_model()
        .objects.filter(is_superuser=True, email__isnull=False)
        .values_list("email", flat=True)
    )
    if superusers:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=list(superusers),
            fail_silently=True,
        )
