# coding=utf-8
"""IUCN Status model definition.

"""

from django.db import models
from django.dispatch import receiver
from colorfield.fields import ColorField

SENSITIVE_STATUS = ['CR', 'EN', 'VU']
IUCN_CATEGORIES = {
    'least concern': 'LC',
    'near threatened': 'NT',
    'vulnerable': 'VU',
    'endangered': 'EN',
    'critically endangered': 'CR',
    'extinct in the wild': 'EW',
    'extinct': 'EX',
    'data deficient': 'DD',
    'not evaluated': 'NE'
}


class IUCNStatus(models.Model):
    """IUCN status model."""
    CATEGORY_CHOICES = (
        (IUCN_CATEGORIES['least concern'], 'Least concern'),
        (IUCN_CATEGORIES['near threatened'], 'Near threatened'),
        (IUCN_CATEGORIES['vulnerable'], 'Vulnerable'),
        (IUCN_CATEGORIES['endangered'], 'Endangered'),
        (IUCN_CATEGORIES['critically endangered'], 'Critically endangered'),
        (IUCN_CATEGORIES['extinct in the wild'], 'Extinct in the wild'),
        (IUCN_CATEGORIES['extinct'], 'Extinct'),
        (IUCN_CATEGORIES['data deficient'], 'Data deficient'),
        (IUCN_CATEGORIES['not evaluated'], 'Not evaluated')
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
