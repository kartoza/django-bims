# coding=utf-8
"""Sass biotope model definition.
"""
from django.contrib.gis.db import models
from sass.models.abstract_additional_data import AbstractAdditionalData
from bims.models.taxon_group import TaxonGroup

BIOTOPE_TYPE_BROAD = 'broad'
BIOTOPE_TYPE_SPECIFIC = 'specific'
BIOTOPE_TYPE_SUBSTRATUM = 'substratum'


class BiotopeQuerySet(models.QuerySet):
    def biotope_list(self, taxon_group, biotope_type):
        if not isinstance(taxon_group, TaxonGroup):
            return []
        return list(self.filter(
            taxon_group=taxon_group,
            biotope_type=biotope_type
        ).values('id', 'name').order_by('display_order'))


class BiotopeManager(models.Manager):
    def get_queryset(self):
        return BiotopeQuerySet(self.model, using=self._db)

    def broad_biotope_list(self, taxon_group):
        return self.get_queryset().biotope_list(
            taxon_group,
            BIOTOPE_TYPE_BROAD
        )

    def specific_biotope_list(self, taxon_group):
        return self.get_queryset().biotope_list(
            taxon_group,
            BIOTOPE_TYPE_SPECIFIC
        )

    def substratum_list(self, taxon_group):
        return self.get_queryset().biotope_list(
            taxon_group,
            BIOTOPE_TYPE_SUBSTRATUM
        )


class Biotope(AbstractAdditionalData):
    """Sass Biotope model."""
    BIOTOPE_FORM_CHOICES = (
        ('0', '0'),
        ('1', '1'),  # SASS Form
        ('2', '2')   # SASS Form
    )

    BIOTOPE_TYPE_CHOICES = (
        (BIOTOPE_TYPE_BROAD, 'Broad'),
        (BIOTOPE_TYPE_SPECIFIC, 'Specific'),
        (BIOTOPE_TYPE_SUBSTRATUM, 'Substratum')
    )

    name = models.CharField(
        max_length=200,
        blank=False,
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    display_order = models.FloatField(
        null=True,
        blank=True
    )

    biotope_form = models.CharField(
        max_length=2,
        choices=BIOTOPE_FORM_CHOICES,
        blank=True,
    )

    biotope_type = models.CharField(
        max_length=10,
        choices=BIOTOPE_TYPE_CHOICES,
        blank=True,
    )

    biotope_component = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    broad = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    specific = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    substratum = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    taxon_group = models.ManyToManyField(
        'bims.TaxonGroup',
        null=True,
        blank=True
    )

    objects = BiotopeManager()

    verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


def merge_biotope(excluded: Biotope = None, biotopes: BiotopeQuerySet = None):
    from django.db.models.fields.reverse_related import ForeignObjectRel
    from bims.utils.logger import log
    """
    Merge multiple biotopes
    """
    if not excluded:
        return
    if not biotopes:
        return
    biotopes = biotopes.exclude(id=excluded.id)

    if biotopes.count() < 1:
        return

    log('Merging %s data' % biotopes.count())

    links = [
        rel.get_accessor_name() for rel in excluded._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for biotope in biotopes:
            log('----- {} -----'.format(str(biotope)))
            for link in links:
                try:
                    objects = getattr(biotope, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {sampling_method}'.format(
                            obj=str(objects.model._meta.label),
                            sampling_method=str(biotope)
                        ))
                        update_dict = {
                            getattr(
                                biotope, link
                            ).field.name: excluded
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            log(''.join(['-' for i in range(len(str(biotope)) + 12)]))

    biotopes.delete()
