__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '26/02/18'

from datetime import date

import json
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.core.exceptions import ValidationError


class Profile(models.Model):
    ROLE_CHOICES = (
        ('water_resource_manager', 'Water Resource Manager'),
        ('researcher', 'Researcher'),
        ('consultant', 'Consultant'),
        ('conservation_planner', 'Conservation Planner'),
        ('citizen', 'Citizen'),
    )
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
    sass_accredited_date_from = models.DateField(
        null=True,
        blank=True
    )
    sass_accredited_date_to = models.DateField(
        null=True,
        blank=True
    )
    hide_bims_info = models.BooleanField(
        default=False
    )
    role = models.CharField(
        max_length=100,
        choices=ROLE_CHOICES,
        blank=True,
        null=True,
    )

    def is_accredited(self):
        if (
            not self.sass_accredited_date_to or
            not self.sass_accredited_date_from
        ):
            return False
        if self.sass_accredited_date_from > self.sass_accredited_date_to:
            return False
        if self.sass_accredited_date_to > date.today():
            return True

    def accredit(
            self,
            date_accredit_from=None,
            date_accredit_to=None):
        """
        Accredit user
        :param date_accredit_from: accredited user start date
        :param date_accredit_to: accredited user end date
        """
        if not date_accredit_to:
            self.sass_accredited_date_to = date(date.today().year, 12, 31)
        else:
            if date_accredit_to <= date.today():
                self.sass_accredited_date_to = date(date.today().year, 12, 31)
            else:
                self.sass_accredited_date_to = date_accredit_to
        if self.sass_accredited_date_from:
            # If we already have accreditation start date, no need to update it
            self.save()
            return

        if not date_accredit_from:
            self.sass_accredited_date_from = date(date.today().year, 1, 1)
        else:
            self.sass_accredited_date_from = date_accredit_from
        self.save()

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

    def clean(self):
        if self.sass_accredited_date_from and not self.sass_accredited_date_to:
            raise ValidationError(
                'Missing SASS Accredited date to'
            )
        if self.sass_accredited_date_to and not self.sass_accredited_date_from:
            raise ValidationError(
                'Missing SASS Accredited date from'
            )
        if self.sass_accredited_date_from > self.sass_accredited_date_to:
            raise ValidationError(
                'SASS Accredited date from should be '
                'before SASS Accredited date to'
            )

    class Meta:
        app_label = 'bims'
        permissions = (
            ('get_all_email', 'Get all email'),
        )

    def __unicode__(self):
        return u'%s' % self.qualifications
