# coding=utf-8
"""IUCN Status model definition.

"""

from django.db import models
from django.dispatch import receiver
from colorfield.fields import ColorField
from ordered_model.models import OrderedModel

SENSITIVE_STATUS = ['CR', 'EN', 'VU']
IUCN_CATEGORIES = {
    'least concern': 'LC',
    'near threatened': 'NT',
    'vulnerable': 'VU',
    'endangered': 'EN',
    'critically endangered': 'CR',
    'critically endangered, possibly extinct': 'CR PE',
    'extinct in the wild': 'EW',
    'extinct': 'EX',
    'regionally extinct': 'RE',
    'critically rare': 'CA',
    'rare': 'RA',
    'declining': 'D',
    'data deficient': 'DD',
    'data deficient - insufficient information': 'DDD',
    'data deficient - taxonomically problematic': 'DDT',
    'not evaluated': 'NE',
    'conservation dependent': 'LR/cd',
    'near threatened - legacy': 'LR/nt',
    'least concern - legacy': 'LR/lc',
}


class IUCNStatus(OrderedModel):
    """IUCN status model."""
    CATEGORY_CHOICES = (
        (IUCN_CATEGORIES['least concern'], 'Least Concern'),
        (IUCN_CATEGORIES['near threatened'], 'Near Threatened'),
        (IUCN_CATEGORIES['vulnerable'], 'Vulnerable'),
        (IUCN_CATEGORIES['endangered'], 'Endangered'),
        (IUCN_CATEGORIES['critically endangered'], 'Critically Endangered'),
        (IUCN_CATEGORIES['critically endangered, possibly extinct'],
         'Critically Endangered, Possibly Extinct'),
        (IUCN_CATEGORIES['extinct in the wild'], 'Extinct in the Wild'),
        (IUCN_CATEGORIES['extinct'], 'Extinct'),
        (IUCN_CATEGORIES['regionally extinct'], 'Regionally Extinct'),
        (IUCN_CATEGORIES['critically rare'], 'Critically Rare'),
        (IUCN_CATEGORIES['rare'], 'Rare'),
        (IUCN_CATEGORIES['declining'], 'Declining'),
        (IUCN_CATEGORIES['data deficient'], 'Data Deficient'),
        (IUCN_CATEGORIES['data deficient - insufficient information'],
         'Data Deficient - Insufficient Information'),
        (IUCN_CATEGORIES['data deficient - taxonomically problematic'],
         'Data Deficient - Taxonomically Problematic'),
        (IUCN_CATEGORIES['not evaluated'], 'Not Evaluated'),
        (IUCN_CATEGORIES['conservation dependent'], 'Conservation Dependent'),
        (IUCN_CATEGORIES['near threatened - legacy'], 'Near Threatened - Legacy'),
        (IUCN_CATEGORIES['least concern - legacy'], 'Least Concern - Legacy'),
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

    national = models.BooleanField(
        default=False
    )

    def get_status(self):
        """"Return status name."""
        choices_dict = {}
        for choice, value in self.CATEGORY_CHOICES:
            choices_dict[choice] = value
        if self.category in choices_dict:
            return choices_dict[self.category]
        return self.category

    def __str__(self):
        return u'%s' % self.category

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'IUCN Status'
        verbose_name = 'IUCN Status'
        ordering = ['order']


@receiver(models.signals.pre_save, sender=IUCNStatus)
def iucn_status_pre_save_handler(sender, instance, **kwargs):
    if instance.category:
        # if the category is Critically Endangered or Endangered or
        # Vulnerable then the iucn status is sensitive
        if instance.category in SENSITIVE_STATUS:
            instance.sensitive = True
        else:
            instance.sensitive = False
