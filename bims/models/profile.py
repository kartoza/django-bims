__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '26/02/18'

from datetime import date

import json
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import JSONField
from django.db import models
from django.core.exceptions import ValidationError
from ordered_model.models import OrderedModel


class Role(OrderedModel):
    name = models.CharField(
        max_length=100, unique=True)
    display_name = models.CharField(
        max_length=100)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.display_name.lower().replace(' ', '_')
        super().save(*args, **kwargs)


class Profile(models.Model):
    ROLE_CHOICES = (
        ('water_resource_manager', 'Water Resource Manager'),
        ('researcher', 'Researcher'),
        ('consultant', 'Consultant'),
        ('conservation_planner', 'Conservation Planner'),
        ('citizen', 'Citizen'),
        ('national_park_management', 'National Park management'),
        ('district_environmental_officer', 'District Environmental Officer'),
        ('government_staff', 'Government staff'),
        ('academic_staff', 'Academic staff'),
        ('policy_maker', 'Policy maker')
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
        default=dict,
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
    role = models.ForeignKey(
        'bims.Role',
        on_delete=models.CASCADE,
        null=True
    )
    signup_source_site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The source site where the user signed up. For tracking user registration origins."
    )

    @property
    def first_name(self):
        if self.user:
            return self.user.first_name
        return '-'

    @property
    def last_name(self):
        if self.user:
            return self.user.last_name
        return '-'

    def is_accredited(self, collection_date = None):
        if (
            not self.sass_accredited_date_to or
            not self.sass_accredited_date_from
        ):
            return False
        if self.sass_accredited_date_from and self.sass_accredited_date_to:
            if self.sass_accredited_date_from > self.sass_accredited_date_to:
                return False
        else:
            return False
        if collection_date and self.sass_accredited_date_to > collection_date:
            return True
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
            if date_accredit_to:
                self.sass_accredited_date_from = date(
                    date_accredit_to.year, 1, 1
                )
            else:
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
        if (
            not self.sass_accredited_date_from and
            not self.sass_accredited_date_to
        ):
            return
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
