import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sites.models import Site
from django.http import Http404
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.api_views.taxon_update import create_taxon_proposal
from bims.models import (
    TaxonGroup, Taxonomy, BiologicalCollectionRecord,
    TaxonExtraAttribute, TaxonomicGroupCategory,
    TaxonomyUpdateProposal, OccurrenceUploadTemplate
)


def update_taxon_group_orders(taxon_group_ids):
    """
    Update taxon group orders
    :param taxon_group_ids: list of taxon taxon group ids
    """
    taxon_groups = TaxonGroup.objects.filter(
        id__in=taxon_group_ids
    )
    for taxon_group in taxon_groups:
        try:
            order = taxon_group_ids.index(taxon_group.id)
            taxon_group.display_order = order
            taxon_group.save()
        except ValueError:
            continue


def remove_taxa_from_taxon_group(taxa_ids, taxon_group_id):
    """
    Remove taxa from taxon group
    :param taxa_ids: list of taxon taxon ids
    :param taxon_group_id: id of the taxon group
    """
    taxa = Taxonomy.objects.filter(
        id__in=taxa_ids
    )
    try:
        taxon_group = TaxonGroup.objects.get(
            id=taxon_group_id
        )
    except TaxonGroup.DoesNotExist:
        return
    for taxonomy in taxa:
        taxon_group.taxonomies.remove(taxonomy)
        BiologicalCollectionRecord.objects.filter(
            taxonomy=taxonomy
        ).update(module_group=None)


def add_taxa_to_taxon_group(taxa_ids, taxon_group_id):
    """
    Add taxa to taxon group
    :param taxa_ids: list of taxon taxon ids
    :param taxon_group_id: id of the taxon group
    """
    taxa = Taxonomy.objects.filter(
        id__in=taxa_ids
    )
    try:
        taxon_group = TaxonGroup.objects.get(
            id=taxon_group_id
        )
    except TaxonGroup.DoesNotExist:
        return
    for taxonomy in taxa:
        if not taxon_group.taxonomies.filter(
            id=taxonomy.id
        ).exists():
            create_taxon_proposal(taxonomy, taxon_group)
        taxon_group.taxonomies.add(
            taxonomy,
            through_defaults={
                'is_validated': False
            }
        )


class TaxaUpdateMixin(UserPassesTestMixin, APIView):
    def test_func(self):
        return self.request.user.has_perm('bims.change_taxongroup')


class UpdateTaxonGroupOrder(TaxaUpdateMixin):
    """Api to update taxon groups order.
    Post data required:
    {
        'taxonGroups': [1,2] // List of taxon groups id sorted by their order
    }
    """
    def post(self, request, *args):
        taxon_groups_array = self.request.POST.get('taxonGroups', None)
        if not taxon_groups_array:
            raise Http404('Missing taxon groups')
        taxon_group_ids = json.loads(taxon_groups_array)
        update_taxon_group_orders(taxon_group_ids)
        return Response('Updated')


class RemoveTaxaFromTaxonGroup(TaxaUpdateMixin):
    """Api to remove taxa from taxon group.
    Post data required:
    {
        'taxaIds': [1,2], // List of taxa id
        'taxonGroupId': 1 // id of the taxon group
    }
    """
    def post(self, request, *args):
        taxa_ids = self.request.POST.get('taxaIds', None)
        taxon_group_id = self.request.POST.get('taxonGroupId', None)
        if not taxa_ids or not taxon_group_id:
            raise Http404('Missing required parameter')
        taxa_ids = json.loads(taxa_ids)
        taxon_group_id = int(taxon_group_id)
        remove_taxa_from_taxon_group(taxa_ids, taxon_group_id)
        return Response(
            {
                'taxonomy_count': TaxonGroup.objects.get(
                    id=taxon_group_id
                ).taxonomies.all().count()
            }
        )


class AddTaxaToTaxonGroup(TaxaUpdateMixin):
    """Api to add taxa to taxon group.
    Post data required:
    {
        'taxaIds': [1,2], // List of taxa id
        'taxonGroupId': 1 // id of the taxon group
    }
    """
    def post(self, request, *args):
        taxa_ids = self.request.POST.get('taxaIds', None)
        taxon_group_id = self.request.POST.get('taxonGroupId', None)
        if not taxa_ids or not taxon_group_id:
            raise Http404('Missing required parameter')
        taxa_ids = json.loads(taxa_ids)
        taxon_group_id = int(taxon_group_id)
        add_taxa_to_taxon_group(taxa_ids, taxon_group_id)
        return Response(
            {
                'taxonomy_count': TaxonGroup.objects.get(
                    id=taxon_group_id
                ).taxonomies.all().count()
            }
        )



class UpdateTaxonGroup(TaxaUpdateMixin):
    """
    API to update or add a new taxon group.

    POST form-data:
    - module_id (optional): if provided, update that TaxonGroup; if not, create new.
    - module_name
    - module_logo (file)
    - parent-taxon (id)
    - gbif-species (taxonomy id)
    - extra_attribute: can repeat multiple times
    - taxon-group-experts: can repeat multiple times
    - taxa_upload_template: file
    - occurrence_upload_template: file           [legacy single upload]
    - occurrence_upload_templates: <multiple files> [new multi-upload]
    - delete_occurrence_template: <id> repeated   [mark rows to delete]
    """

    def post(self, request, *args):
        module_name = request.POST.get('module_name')
        module_logo = request.FILES.get('module_logo', None)
        module_id = request.POST.get('module_id', None)
        extra_attributes = request.POST.getlist('extra_attribute', [])
        new_expert_ids = request.POST.getlist('taxon-group-experts', [])
        gbif_species = request.POST.get('gbif-species', None)
        parent_taxon_id = request.POST.get('parent-taxon', None)

        taxa_upload_template = request.FILES.get('taxa_upload_template', None)

        legacy_occurrence_upload_template = request.FILES.get(
            'occurrence_upload_template', None
        )

        occurrence_upload_templates_files = request.FILES.getlist(
            'occurrence_upload_templates'
        )

        delete_occurrence_template_ids = request.POST.getlist(
            'delete_occurrence_template', []
        )

        if module_id:
            try:
                taxon_group = TaxonGroup.objects.get(id=module_id)
            except TaxonGroup.DoesNotExist:
                raise Http404('Taxon group does not exist')
        else:
            taxon_group = TaxonGroup()

        taxon_group.site = Site.objects.get_current()

        if not taxon_group.parent:
            taxon_group.category = TaxonomicGroupCategory.SPECIES_MODULE.name

        if module_name:
            taxon_group.name = module_name

        if module_logo:
            taxon_group.logo = module_logo

        if gbif_species:
            taxon_group.gbif_parent_species_id = gbif_species

        if taxa_upload_template:
            taxon_group.taxa_upload_template = taxa_upload_template

        if legacy_occurrence_upload_template:
            taxon_group.occurrence_upload_template = legacy_occurrence_upload_template

        if parent_taxon_id:
            try:
                parent_taxon_group = TaxonGroup.objects.get(id=parent_taxon_id)
                taxon_group.parent = parent_taxon_group
            except TaxonGroup.DoesNotExist:
                pass
        else:
            taxon_group.parent = None

        taxon_group.save()

        TaxonExtraAttribute.objects.filter(
            taxon_group=taxon_group
        ).exclude(
            name__in=extra_attributes
        ).delete()

        for extra_attr in extra_attributes:
            if not extra_attr:
                continue
            try:
                TaxonExtraAttribute.objects.get_or_create(
                    taxon_group=taxon_group,
                    name=extra_attr
                )
            except TaxonExtraAttribute.MultipleObjectsReturned:
                pass

        if delete_occurrence_template_ids:
            OccurrenceUploadTemplate.objects.filter(
                taxon_group=taxon_group,
                id__in=delete_occurrence_template_ids
            ).delete()

        for f in occurrence_upload_templates_files:
            if not f:
                continue
            OccurrenceUploadTemplate.objects.create(
                taxon_group=taxon_group,
                file=f,
                label=''
            )

        if new_expert_ids:
            cleaned_expert_ids = []
            for expert_id in new_expert_ids:
                try:
                    cleaned_expert_ids.append(int(expert_id))
                except (ValueError, TypeError):
                    continue
            taxon_group.experts.set(cleaned_expert_ids)
        else:
            taxon_group.experts.clear()

        return Response(
            'Taxon group updated' if module_id else 'New taxon group added'
        )
