import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sites.models import Site
from django.http import Http404
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models import (
    TaxonGroup, Taxonomy, BiologicalCollectionRecord,
    TaxonExtraAttribute, TaxonomicGroupCategory,
    TaxonomyUpdateProposal
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
            with transaction.atomic():
                TaxonomyUpdateProposal.objects.get_or_create(
                    scientific_name=taxonomy.scientific_name,
                    canonical_name=taxonomy.canonical_name,
                    legacy_canonical_name=taxonomy.legacy_canonical_name,
                    original_taxonomy=taxonomy,
                    rank=taxonomy.rank,
                    taxonomic_status=taxonomy.taxonomic_status,
                    endemism=taxonomy.endemism,
                    iucn_status=taxonomy.iucn_status,
                    accepted_taxonomy=taxonomy.accepted_taxonomy,
                    parent=taxonomy.parent,
                    taxon_group=taxon_group,
                    new_data=True,
                    status='pending',
                    taxon_group_under_review=taxon_group,
                    gbif_key=taxonomy.gbif_key,
                    origin=taxonomy.origin
                )
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
    """Api to update taxon group.
    API to update or add a new taxon group.
    For updating, 'module_id' is required in POST data.
    To add a new module, omit 'module_id'.

    Post data required:
    {
        'module_id': id
    }
    Post data optional:
    {
        'module_name': 'Module' // Name of the taxon group
        'module_logo': File img // Img file of the logo
    }
    """
    def post(self, request, *args):
        module_name = self.request.POST.get('module_name')
        module_logo = self.request.FILES.get('module_logo', None)
        module_id = self.request.POST.get('module_id', None)
        extra_attributes = self.request.POST.getlist('extra_attribute', [])
        new_expert_ids = self.request.POST.getlist('taxon-group-experts')
        gbif_species = self.request.POST.get('gbif-species', None)
        parent_taxon_id = self.request.POST.get('parent-taxon', None)
        taxa_upload_template = self.request.FILES.get('taxa_upload_template', None)
        occurrence_upload_template = self.request.FILES.get('occurrence_upload_template', None)

        if module_id:
            # Update existing module
            try:
                taxon_group = TaxonGroup.objects.get(id=module_id)
                taxon_group.gbif_parent_species_id = gbif_species
            except TaxonGroup.DoesNotExist:
                raise Http404('Taxon group does not exist')
        else:
            # Create new module
            taxon_group = TaxonGroup()

        taxon_group.site = Site.objects.get_current()
        if not taxon_group.parent:
            taxon_group.category = TaxonomicGroupCategory.SPECIES_MODULE.name

        if module_name:
            taxon_group.name = module_name

        if module_logo:
            taxon_group.logo = module_logo

        if taxa_upload_template:
            taxon_group.taxa_upload_template = taxa_upload_template

        if occurrence_upload_template:
            taxon_group.occurrence_upload_template = occurrence_upload_template

        TaxonExtraAttribute.objects.filter(taxon_group=taxon_group).exclude(
            name__in=extra_attributes).delete()

        if extra_attributes:
            taxon_group.save()
            for extra_attribute in extra_attributes:
                if not extra_attribute:
                    continue
                try:
                    TaxonExtraAttribute.objects.get_or_create(
                        name=extra_attribute,
                        taxon_group=taxon_group
                    )
                except TaxonExtraAttribute.MultipleObjectsReturned:
                    pass

        if parent_taxon_id:
            try:
                parent_taxon_group = TaxonGroup.objects.get(
                    id=parent_taxon_id
                )
                taxon_group.parent = parent_taxon_group
            except TaxonGroup.DoesNotExist:
                pass
        else:
            taxon_group.parent = None

        taxon_group.save()

        new_expert_ids = [int(expert_id) for expert_id in new_expert_ids]
        taxon_group.experts.set(new_expert_ids)

        return Response('Taxon group updated' if module_id else 'New taxon group added')
