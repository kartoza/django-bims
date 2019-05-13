__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '26/02/18'

import json
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
    sass_accredited_time = models.DateField(
        null=True,
        blank=True
    )
    hide_bims_info = models.BooleanField(
        default=False
    )

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not self.data:
                break
            if isinstance(self.data, dict):
                is_dictionary = True
            else:
                self.data = json.loads(self.data)
                attempt += 1
        super(Profile, self).save(*args, **kwargs)

    class Meta:
        app_label = 'bims'

    def __unicode__(self):
        return u'%s' % self.qualifications
