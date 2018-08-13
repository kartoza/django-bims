# coding=utf-8
"""IUCN Status model definition.

"""

from django.db import models
from django.dispatch import receiver
from colorfield.fields import ColorField

SENSITIVE_STATUS = ['CR', 'EN', 'VU']


class IUCNStatus(models.Model):
    """IUCN status model."""
    CATEGORY_CHOICES = (
        ('LC', 'Least Concern'),
        ('NT', 'Near Threatened'),
        ('VU', 'Vulnerable'),
        ('EN', 'Endangered'),
        ('CR', 'Critically Endangered'),
        ('EW', 'Extinct In The Wild'),
        ('EX', 'Extinct'),
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        default='',
    )
    sensitive = models.BooleanField(
        default=False
    )
    colour = ColorField(default='#009106')

    def get_status(self):
        """"Return status name."""
        choices_dict = {}
        for choice, value in self.CATEGORY_CHOICES:
            choices_dict[choice] = value
        return choices_dict[self.category]

    def __str__(self):
        return u'%s' % self.category

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'IUCN Status'
        verbose_name = 'IUCN Status'


@receiver(models.signals.pre_save, sender=IUCNStatus)
def iucn_status_pre_save_handler(sender, instance, **kwargs):
    if instance.category:
        # if the category is Critically Endangered or Endangered or
        # Vulnerable then the iucn status is sensitive
        if instance.category in SENSITIVE_STATUS:
            instance.sensitive = True
        else:
            instance.sensitive = False
