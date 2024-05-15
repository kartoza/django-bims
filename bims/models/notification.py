from typing import List

from django.contrib.sites.models import Site
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Notification Choices
SITE_VISIT_VALIDATION = 'SITE_VISIT_VALIDATION'
SITE_VALIDATION = 'SITE_VALIDATION'
NEW_TAXONOMY = 'NEW_TAXONOMY'
DOWNLOAD_REQUEST = 'DOWNLOAD_REQUEST'
ACCOUNT_CREATED = 'ACCOUNT_CREATED'
SASS_CREATED = 'SASS_CREATED'
WETLAND_ISSUE_CREATED = 'WETLAND_ISSUE_CREATED'

NOTIFICATION_TYPES = (
    (SITE_VISIT_VALIDATION, 'Site visit is ready to be validated'),
    (SITE_VALIDATION, 'Site is ready to be validated'),
    (DOWNLOAD_REQUEST, 'Download request notification'),
    (ACCOUNT_CREATED, 'Account created email notification'),
    (SASS_CREATED, 'SASS created email notification'),
    (NEW_TAXONOMY, 'New taxonomy email notification'),
    (WETLAND_ISSUE_CREATED, 'New wetland issue email notification'),
)


class Notification(models.Model):
    name = models.CharField(
        max_length=255,
        choices=NOTIFICATION_TYPES,
        unique=True
    )
    description = models.TextField(
        blank=True
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='notifications',
        blank=False
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    @property
    def user_emails(self):
        return [user.email for user in self.users.all()]

    def __str__(self):
        return self.name


def get_recipients_for_notification(
        notification_name: str,
        site: Site = None
) -> List[str]:
    """
    Fetches the recipient emails for a given notification type.

    If the specific notification type isn't found, returns the emails of
        all superusers as a fallback.

    Args:
    - notification_name (str): The name of the notification type to
        fetch recipients for.
    - site (Site, optional): The current site instance. Defaults to the current site.

    Returns:
    - List[str]: A list of email addresses.
    """
    if site is None:
        site = Site.objects.get_current()

    try:
        # Attempt to find the notification for the specified site
        recipients = Notification.objects.get(
            name=notification_name,
            site=site
        ).user_emails
    except Notification.DoesNotExist:
        # If not found, attempt to find a site-agnostic notification
        notification = Notification.objects.filter(
            name=notification_name,
            site__isnull=True
        ).first()
        if notification:
            recipients = notification.user_emails
        else:
            # If still not found, return superuser emails
            recipients = list(
                get_user_model().objects.filter(
                    is_superuser=True
                ).values_list('email', flat=True)
            )
    return recipients
