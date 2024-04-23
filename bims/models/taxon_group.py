# coding=utf-8
"""Taxon group model definition.

"""
from django.conf import settings
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


TAXON_GROUP_LEVEL_1 = 'level_1'
TAXON_GROUP_LEVEL_2 = 'level_2'
TAXON_GROUP_LEVEL_3 = 'level_3'


class TaxonGroup(models.Model):

    CHART_CHOICES = (
        ('conservation status', 'Conservation Status'),
        ('division', 'Division'),
        ('sass', 'SASS'),
        ('origin', 'Origin'),
        ('endemism', 'Endemism'),
    )

    LEVEL_CHOICES = (
        (TAXON_GROUP_LEVEL_1, 'Level 1: Organism'),
        (TAXON_GROUP_LEVEL_2, 'Level 2: Regions and/or ecosystem type'),
        (TAXON_GROUP_LEVEL_3, 'Level 3: Country'),
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
        blank=True,
        through='bims.TaxonGroupTaxonomy',
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

    additional_sites = models.ManyToManyField(
        to=Site,
        related_name='additional_sites',
        blank=True,
        help_text="A list of additional sites associated with this taxon group."
    )

    level = models.CharField(
        help_text='Level of the taxon group',
        max_length=100,
        choices=LEVEL_CHOICES,
        null=True,
        blank=True
    )

    parent = models.ForeignKey(
        verbose_name='Parent',
        to='self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    experts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
    )

    gbif_parent_species = models.ForeignKey(
        'bims.Taxonomy',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taxon_groups',
        help_text='Used to fetch species from GBIF'
    )

    class Meta:
        ordering = ('display_order',)
        permissions = (
            ('can_validate_taxon_group', 'Can validate taxon group'),
        )

    def __str__(self):
        return f'{self.name} - {self.level}'

    def get_top_level_parent(self):
        """
        Recursively finds the top-level parent of the current taxon group.

        If the current taxon group is a top-level group (has no parent),
        it returns itself.

        :return: TaxonGroup: The top-level parent taxon group.
        """
        if not self.parent:
            return self
        else:
            return self.parent.get_top_level_parent()

    def get_all_experts(self) -> set:
        """
        Recursively collects all unique experts from the current
        TaxonGroup and its entire ancestry.

        :return: A set of unique expert objects associated with the
            TaxonGroup and its ancestors.
        """
        all_experts = set()

        def collect_experts(current_taxon_group):
            all_experts.update(current_taxon_group.experts.all())

            if current_taxon_group.parent:
                collect_experts(current_taxon_group.parent)

        collect_experts(self)
        return all_experts

    @property
    def permission_name(self):
        return f'Can validate {self.name} - {self.level}'

    @property
    def group_name(self):
        levels = dict(TaxonGroup.LEVEL_CHOICES)
        if self.level and self.level in levels:
            level = levels[self.level]
        else:
            level = ''
        return f'{level} : {self.name}'

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
                    current_instance.level != instance.level
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
                if instance.level:
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

    from bims.api_views.module_summary import ModuleSummary

    if not issubclass(sender, TaxonGroup):
        return

    module_summary_api = ModuleSummary()
    module_summary_api.call_summary_data_in_background()

    if not instance.site:
        return

    assign_site_to_uncategorized_records.delay(
        instance.id, instance.site_id
    )

    if instance.level in (
        TAXON_GROUP_LEVEL_1,
        TAXON_GROUP_LEVEL_2,
        TAXON_GROUP_LEVEL_3
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
