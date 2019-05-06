__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '26/02/18'

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bims_profile')
    qualifications = models.CharField(
        max_length=250,
        blank=True,
        default='',
        null=True,
    )
    other = models.CharField(
        max_length=100,
        blank=True,
        default='',
        null=True,
    )
    full_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        null=True,
    )
    data = JSONField(
        default='',
        null=True,
        blank=True,
    )
    sass_accredited = models.BooleanField(
        verbose_name='SASS Accredited',
        default=False
    )
    hide_bims_info = models.BooleanField(
        default=False
    )

    class Meta:
        app_label = 'bims'

    def __unicode__(self):
        return u'%s' % self.qualifications
