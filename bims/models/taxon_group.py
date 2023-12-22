# coding=utf-8
"""Taxon group model definition.

"""
from django.contrib.auth.models import Permission, Group
from django.contrib.gis.db import models
from django.contrib.sites.models import Site
from django.dispatch import receiver

from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.tasks.collection_record import (
    assign_site_to_uncategorized_records
)
from bims.permissions.generate_permission import generate_permission
from bims.utils.decorator import prevent_recursion


class TaxonGroup(models.Model):

    CHART_CHOICES = (
        ('conservation status', 'Conservation Status'),
        ('division', 'Division'),
        ('sass', 'SASS'),
        ('origin', 'Origin'),
        ('endemism', 'Endemism'),
    )

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    singular_name = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    category = models.CharField(
        verbose_name='Taxonomic Group Category',
        max_length=50,
        choices=[(rank.name, rank.value) for rank in TaxonomicGroupCategory],
        blank=True,
    )

    logo = models.ImageField(
        upload_to='module_logo',
        null=True,
        blank=True
    )

    taxonomies = models.ManyToManyField(
        'bims.Taxonomy',
        blank=True
    )

    source_collection = models.CharField(
        help_text='Additional filter for search collections',
        max_length=200,
        null=True,
        blank=True
    )

    display_order = models.IntegerField(
        null=True,
        blank=True
    )

    chart_data = models.CharField(
        help_text='Data to display on chart',
        max_length=100,
        choices=CHART_CHOICES,
        null=True,
        blank=True,
        default=''
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Associated Site",
        help_text="The site this taxon group is associated with."
    )

    parent = models.ForeignKey(
        verbose_name='Parent',
        to='self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('display_order',)
        permissions = (
            ('can_validate_taxon_group', 'Can validate taxon group'),
        )

    def __str__(self):
        return f'{self.name} - {self.category}'

    @property
    def permission_name(self):
        return f'Can validate {self.name} - {self.category}'

    @property
    def group_name(self):
        taxon_group_categories = dict(
            (rank.name, rank.value) for rank in TaxonomicGroupCategory)
        return f'{taxon_group_categories[self.category]} : {self.name}'

    @property
    def permission_codename(self):
        return self.permission_name.lower().replace(' ', '_')


@receiver(models.signals.pre_save)
def taxon_group_pre_save(sender, instance: TaxonGroup, **kwargs):
    if not issubclass(sender, TaxonGroup):
        return

    if instance.pk:
        current_instance = TaxonGroup.objects.filter(
            pk=instance.pk).first()

        if current_instance:
            if (
                current_instance.name != instance.name or
                    current_instance.category != instance.category
            ):
                old_permission_codename = (
                    current_instance.permission_codename
                )
                new_permission_codename = (
                    instance.permission_codename
                )
                new_permission_name = instance.permission_name
                Permission.objects.filter(
                    codename=old_permission_codename
                ).update(
                    name=new_permission_name,
                    codename=new_permission_codename
                )
                old_group_name = current_instance.group_name
                Group.objects.filter(
                    name=old_group_name
                ).update(
                    name=instance.group_name
                )


def add_permission_to_parent(taxon_group: TaxonGroup, permission: Permission):
    if taxon_group.parent:
        add_permission_to_parent(taxon_group.parent, permission)
    group = Group.objects.filter(
        name=taxon_group.group_name
    ).first()
    if group:
        group.permissions.add(permission)


@receiver(models.signals.post_save)
@prevent_recursion
def taxon_group_post_save(sender, instance: TaxonGroup, created, **kwargs):
    if not issubclass(sender, TaxonGroup):
        return

    if not instance.site:
        return

    assign_site_to_uncategorized_records.delay(
        instance.id, instance.site_id
    )

    if instance.category in (
        TaxonomicGroupCategory.LEVEL_1_GROUP.name,
        TaxonomicGroupCategory.LEVEL_2_GROUP.name,
        TaxonomicGroupCategory.LEVEL_3_GROUP.name
    ):
        permission = generate_permission(
            instance.permission_name,
            'can_validate_taxon_group'
        )
        group, created = Group.objects.get_or_create(
            name=instance.group_name)
        group.permissions.add(permission)

        if instance.parent:
            add_permission_to_parent(
                instance.parent, permission)
