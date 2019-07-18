from django.db import models
from preferences.models import Preferences


class SiteSetting(Preferences):
    site_notice = models.TextField(
        null=True,
        blank=True
    )
