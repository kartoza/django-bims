import json
from typing import Mapping

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse, Http404

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import TaxonGroupTaxonomy, IUCNStatus, Endemism, VernacularName
from bims.models.taxon_origin import TaxonOrigin
from bims.models.taxonomy import Taxonomy
from bims.models.taxonomy_update_proposal import (
    TaxonomyUpdateProposal
)
from bims.models.taxon_group import TaxonGroup


ADDITIONAL_KEYS = [
    'Taxonomic Comments',
    'Conservation Comments',
    'Biogeographic Comments',
    'Environmental Comments',
    'Taxonomic References',
    'Conservation References',
    'Biogeographic References',
    'Environmental References',
]


def _normalize_canonical_name(base_taxon, proposed_name, rank, taxonomic_status):
    """
    Ensure canonical_name contains genus/species prefix when appropriate.
    """
    name = (proposed_name or '').strip() or (base_taxon.canonical_name or '').strip()
    if not name:
        return name

    rank_l = (rank or base_taxon.rank or '').lower()
    status_l = (taxonomic_status or base_taxon.taxonomic_status or '').lower()

    if status_l == 'accepted':
        if rank_l == 'species':
            if base_taxon.genus_name and base_taxon.genus_name not in name:
                name = f'{base_taxon.genus_name} {name}'
        elif rank_l == 'subspecies':
            if base_taxon.full_species_name and base_taxon.full_species_name not in name:
                name = f'{base_taxon.full_species_name} {name}'
    return name.strip()


AD_PREFIX = "additional_data__"

def _merge_additional(existing: dict | None, data: dict) -> dict:
    """
    Merge 'additional_data' safely from diverse inputs.
    """
    if existing in (None, "", "null"):
        existing = {}
    elif isinstance(existing, str):
        try:
            loaded = json.loads(existing)
            existing = loaded if isinstance(loaded, dict) else {}
        except Exception:
            existing = {}
    elif isinstance(existing, Mapping):
        existing = dict(existing)
    else:
        existing = {}

    if isinstance(data.get("additional_data"), Mapping):
        for k, v in data["additional_data"].items():
            if v not in ("", None, [], {}):
                existing[k] = v

    for k, v in (data.items() if isinstance(data, Mapping) else []):
        if not isinstance(k, str):
            continue
        if k.startswith(AD_PREFIX):
            key = k[len(AD_PREFIX):].replace("_", " ").strip()
            if v not in ("", None, [], {}):
                existing[key] = v

    for k in ADDITIONAL_KEYS:
        if k in data:
            v = data.get(k)
            if isinstance(v, str):
                v = v.strip()
            if v not in ("", None, [], {}):
                existing[k] = v

    return existing


def ensure_accepted_taxonomy_in_group(taxonomy, taxon_group):
    """
    Ensure that if a taxonomy is a synonym, its accepted taxonomy is added to the taxon group.
    This prevents having to reupload entire lists or reharvest species to get accepted names.

    Args:
        taxonomy: The Taxonomy instance (potentially a synonym)
        taxon_group: The TaxonGroup to which the accepted taxonomy should be added

    Returns:
        The accepted_taxonomy if added, None otherwise
    """
    if not taxonomy or not taxon_group:
        return None

    # Check if this taxonomy has an accepted taxonomy (i.e., it's a synonym)
    accepted_taxonomy = taxonomy.accepted_taxonomy
    if not accepted_taxonomy:
        return None

    # Check if the accepted taxonomy is already in the taxon group
    if TaxonGroupTaxonomy.objects.filter(
        taxonomy=accepted_taxonomy,
        taxongroup=taxon_group
    ).exists():
        return accepted_taxonomy

    # Add the accepted taxonomy to the taxon group
    taxon_group.taxonomies.add(
        accepted_taxonomy,
        through_defaults={
            'is_validated': False
        }
    )

    return accepted_taxonomy


@transaction.atomic
def create_taxon_proposal(
    taxon,
    taxon_group,
    data=None,
    iucn_status=None,
    endemism=None,
    creator=None,
):
    data = data or {}

    iucn_status = iucn_status or taxon.iucn_status
    endemism = endemism or taxon.endemism

    taxonomic_status = (data.get('taxonomic_status') or taxon.taxonomic_status or 'ACCEPTED')
    tax_status_l = taxonomic_status.lower()

    if tax_status_l == 'accepted':
        accepted_taxonomy = None
    else:
        accepted_taxonomy = data.get('accepted_taxonomy', getattr(taxon, 'accepted_taxonomy', None))
        # Convert PK to Taxonomy instance if needed
        if accepted_taxonomy and isinstance(accepted_taxonomy, int):
            try:
                accepted_taxonomy = Taxonomy.objects.get(pk=accepted_taxonomy)
            except Taxonomy.DoesNotExist:
                accepted_taxonomy = None

    additional_data = _merge_additional(getattr(taxon, 'additional_data', {}) or {}, data)

    canonical_name = _normalize_canonical_name(
        base_taxon=taxon,
        proposed_name=data.get('canonical_name', taxon.canonical_name),
        rank=data.get('rank', taxon.rank),
        taxonomic_status=taxonomic_status,
    )

    origin_key = data.get('origin')
    if origin_key and isinstance(origin_key, str):
        origin = TaxonOrigin.objects.filter(origin_key=origin_key).first()
    else:
        origin = taxon.origin

    defaults = {
        'author': data.get('author', taxon.author),
        'rank': data.get('rank', taxon.rank),
        'scientific_name': data.get('scientific_name', taxon.scientific_name),
        'canonical_name': canonical_name,
        'origin': origin,
        'iucn_status': iucn_status,
        'endemism': endemism,
        'taxon_group_under_review': taxon_group,
        'taxonomic_status': taxonomic_status,
        'accepted_taxonomy': accepted_taxonomy,
        'parent': data.get('parent', taxon.parent),
        'hierarchical_data': data.get('hierarchical_data', getattr(taxon, 'hierarchical_data', {}) or {}),
        'gbif_data': data.get('gbif_data', getattr(taxon, 'gbif_data', None)),
        'collector_user': creator,
        'additional_data': additional_data,
        'gbif_key': data.get('gbif_key', getattr(taxon, 'gbif_key', None)),
        'fada_id': data.get('fada_id', getattr(taxon, 'fada_id', None)),
        'species_group': data.get('species_group', getattr(taxon, 'species_group', None)),
    }

    proposal, created = TaxonomyUpdateProposal.objects.update_or_create(
        original_taxonomy=taxon,
        taxon_group=taxon_group,
        status='pending',
        defaults=defaults,
    )

    # Ensure accepted taxonomy is added to the taxon group if this is a synonym
    if accepted_taxonomy and taxon_group:
        # Add the accepted taxonomy directly to the group
        if not TaxonGroupTaxonomy.objects.filter(
            taxonomy=accepted_taxonomy,
            taxongroup=taxon_group
        ).exists():
            taxon_group.taxonomies.add(
                accepted_taxonomy,
                through_defaults={
                    'is_validated': False
                }
            )

    if proposal:
        if 'tags' in data:
            proposal.tags.set(data.get('tags') or [])
        else:
            proposal.tags.set(taxon.tags.all())
        if 'biographic_distributions' in data:
            proposal.biographic_distributions.set(data.get('biographic_distributions') or [])
        else:
            proposal.biographic_distributions.set(taxon.biographic_distributions.all())
        if 'common_name' in data:
            common_name = (data.get('common_name') or '').strip()
            if common_name:
                try:
                    vn, _ = VernacularName.objects.get_or_create(
                        name=common_name,
                        defaults={'language': 'eng'}
                    )
                except VernacularName.MultipleObjectsReturned:
                    vn = VernacularName.objects.filter(
                        name=common_name, language='eng').first()
                proposal.vernacular_names.clear()
                if vn:
                    proposal.vernacular_names.add(vn)
        else:
            proposal.vernacular_names.set(
                taxon.vernacular_names.values_list('pk', flat=True)
            )
        proposal.save()

    return proposal


@transaction.atomic
def update_taxon_proposal(
    proposal: 'TaxonomyUpdateProposal',
    data=None,
    iucn_status=None,
    endemism=None,
):
    data = data or {}

    iucn_status = iucn_status or proposal.iucn_status
    endemism = endemism or proposal.endemism

    taxonomic_status = data.get('taxonomic_status', proposal.taxonomic_status)
    tax_status_l = (taxonomic_status or '').lower()

    if tax_status_l == 'accepted':
        accepted_taxonomy = None
    else:
        accepted_taxonomy = data.get('accepted_taxonomy', proposal.accepted_taxonomy)
        # Convert PK to Taxonomy instance if needed
        if accepted_taxonomy and isinstance(accepted_taxonomy, int):
            try:
                accepted_taxonomy = Taxonomy.objects.get(pk=accepted_taxonomy)
            except Taxonomy.DoesNotExist:
                accepted_taxonomy = None

    merged_additional = _merge_additional(getattr(proposal, 'additional_data', {}) or {}, data)

    base_taxon = proposal.original_taxonomy
    new_rank = data.get('rank', proposal.rank)
    canonical_name = _normalize_canonical_name(
        base_taxon=base_taxon,
        proposed_name=data.get('canonical_name', proposal.canonical_name),
        rank=new_rank,
        taxonomic_status=taxonomic_status,
    )

    proposal_origin_key = data.get('origin')
    if proposal_origin_key and isinstance(proposal_origin_key, str):
        proposal_origin = TaxonOrigin.objects.filter(
            origin_key=proposal_origin_key).first()
    else:
        proposal_origin = proposal.origin

    updates = {
        'status': 'pending',
        'author': data.get('author', proposal.author),
        'parent': data.get('parent', proposal.parent),
        'rank': new_rank,
        'scientific_name': data.get('scientific_name', proposal.scientific_name),
        'canonical_name': canonical_name,
        'origin': proposal_origin,
        'iucn_status': iucn_status,
        'endemism': endemism,
        'species_group': data.get('species_group', proposal.species_group),
        'taxonomic_status': taxonomic_status,
        'accepted_taxonomy': accepted_taxonomy,
        'gbif_key': data.get('gbif_key', proposal.gbif_key),
        'fada_id': data.get('fada_id', proposal.fada_id),
        'gbif_data': data.get('gbif_data', proposal.gbif_data),
        'hierarchical_data': data.get('hierarchical_data', proposal.hierarchical_data or {}),
        'additional_data': merged_additional,
    }

    TaxonomyUpdateProposal.objects.filter(id=proposal.id).update(**updates)

    proposal.refresh_from_db()

    # Ensure accepted taxonomy is added to the taxon group if this is a synonym
    if accepted_taxonomy and proposal.taxon_group:
        # Add the accepted taxonomy directly to the group
        if not TaxonGroupTaxonomy.objects.filter(
            taxonomy=accepted_taxonomy,
            taxongroup=proposal.taxon_group
        ).exists():
            proposal.taxon_group.taxonomies.add(
                accepted_taxonomy,
                through_defaults={
                    'is_validated': False
                }
            )

    if 'tags' in data:
        proposal.tags.set(data.get('tags') or [])
    if 'biographic_distributions' in data:
        proposal.biographic_distributions.set(data.get('biographic_distributions') or [])
    if 'common_name' in data:
        common_name = (data.get('common_name') or '').strip()
        if common_name:
            try:
                vn, _ = VernacularName.objects.get_or_create(
                    name=common_name,
                    defaults={'language': 'eng'}
                )
            except VernacularName.MultipleObjectsReturned:
                vn = VernacularName.objects.filter(name=common_name, language='eng').first()
            proposal.vernacular_names.clear()
            if vn:
                proposal.vernacular_names.add(vn)
        else:
            proposal.vernacular_names.clear()

    proposal.save()
    return proposal


def is_expert(user, taxon_group):
    if user.is_superuser:
        return True
    if not taxon_group:
        return False
    return taxon_group.experts.filter(
        id=user.id
    ).exists()


class UpdateTaxon(UserPassesTestMixin, APIView):
    """
    Provides an API endpoint for updating taxon information. Only superusers or
    experts of the specified taxon group are allowed to propose updates to a taxonomy.
    """

    def test_func(self) -> bool:
        """Check if the user has permissions to update the taxon."""
        if self.request.user.is_superuser:
            return True
        taxon_group = get_object_or_404(
            TaxonGroup,
            pk=self.kwargs.get('taxon_group_id')
        )
        return taxon_group.experts.filter(
            id=self.request.user.id
        ).exists()

    def is_taxon_edited(self, taxon: Taxonomy) -> bool:
        """Check if the taxon is currently being edited (has a pending update proposal)."""
        return TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=taxon,
            status='pending'
        ).exists()

    def put(self, request, taxon_id, taxon_group_id, *args) -> Response:
        """Handle PUT request to propose an update to a taxonomy."""
        taxon = get_object_or_404(
            Taxonomy,
            pk=taxon_id
        )
        taxon_group = get_object_or_404(
            TaxonGroup,
            pk=taxon_group_id
        )
        taxon_edited = self.is_taxon_edited(taxon)
        # Check if taxon is still being edited
        if taxon_edited and not is_expert(request.user, taxon_group):
            # if expert
            return Response({
                'message': 'Taxon is still being edited'
            }, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        with transaction.atomic():
            iucn_status = None
            endemism = None
            try:
                iucn_status = IUCNStatus.objects.get(
                    category=data.get('conservation_status')
                )
            except IUCNStatus.DoesNotExist:
                if taxon.iucn_status:
                    iucn_status = taxon.iucn_status

            try:
                endemism = Endemism.objects.get(
                    name=data.get('endemism')
                )
            except Endemism.DoesNotExist:
                if taxon.endemism:
                    endemism = taxon.endemism

            if not taxon_edited:
                proposal = create_taxon_proposal(
                    taxon=taxon,
                    data=data,
                    taxon_group=taxon_group,
                    iucn_status=iucn_status,
                    endemism=endemism,
                    creator=request.user
                )
                TaxonGroupTaxonomy.objects.filter(
                    taxonomy=taxon,
                    taxongroup=taxon_group
                ).update(is_validated=False)
                success_message = (
                    'Taxonomy update proposal created successfully'
                )
            else:
                proposal = TaxonomyUpdateProposal.objects.filter(
                    original_taxonomy=taxon,
                    status='pending'
                ).first()
                update_taxon_proposal(
                    proposal=proposal,
                    data=data,
                    iucn_status=iucn_status,
                    endemism=endemism
                )
                success_message = (
                    'Taxonomy updated successfully'
                )

        return Response(
            {
                'message': success_message,
                'proposal_id': proposal.pk
            },
            status=status.HTTP_202_ACCEPTED)


class ReviewTaxonProposal(UserPassesTestMixin, APIView):
    """
    A view class for reviewing taxonomy update proposals, allowing for approval or rejection.
    """

    def test_func(self) -> bool:
        """
        Determines if the user has permission to review the taxonomy update proposal.
        Superusers can review any proposal, while other users must be experts of the taxon group.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        user = self.request.user
        if user.is_superuser:
            return True

        proposal = self.get_proposal(
            self.kwargs.get('taxonomy_update_proposal_id', None))

        if not proposal or not proposal.taxon_group_under_review:
            return False

        return user in proposal.taxon_group_under_review.experts.all()

    def get_proposal(self, proposal_id=None):
        """
        Retrieves or creates a taxonomy update proposal based on the request parameters.

        Returns:
            TaxonomyUpdateProposal: The proposal instance or None if not found.
        """
        if proposal_id:
            return get_object_or_404(TaxonomyUpdateProposal, pk=proposal_id)

        taxon_id = self.kwargs.get('taxon_id')
        taxon_group_id = self.kwargs.get('taxon_group_id')
        if taxon_id and taxon_group_id:
            try:
                proposal = TaxonomyUpdateProposal.objects.get(
                    original_taxonomy_id=taxon_id,
                    taxon_group_id=taxon_group_id,
                    status='pending'
                )
            except TaxonomyUpdateProposal.DoesNotExist:
                return None
            return proposal

        return None

    def handle_action(self, request, proposal, action) -> str:
        """
        Handles the approval or rejection of a taxonomy update proposal based on the specified action.

        Parameters:
            request (HttpRequest): The request object.
            proposal (TaxonomyUpdateProposal): The proposal instance.
            action (str): The action to perform ('approve' or 'reject').

        Returns:
            message: Message indicating the outcome of the action.
        """
        if action == 'approve':
            proposal.approve(request.user)
            message = 'Taxonomy update proposal approved successfully.'
        else:
            comments = request.data.get('comments', '')
            proposal.reject_data(request.user, comments)
            message = 'Taxonomy update proposal rejected successfully.'

        return message

    def put(self,
            request,
            taxonomy_update_proposal_id=None,
            taxon_id=None,
            taxon_group_id=None) -> JsonResponse:
        """
        Handles PUT requests to update the status of a taxonomy update proposal.

        Parameters:
            request (HttpRequest): The request object.
            taxonomy_update_proposal_id (int, optional): The ID of the taxonomy update proposal.
            taxon_id (int, optional): The ID of the taxon, if provided.
            taxon_group_id (int, optional): The ID of the taxon group, if provided.

        Returns:
            JsonResponse: A response with the outcome message and HTTP status.
        """
        action = request.data.get('action')
        if action not in ['approve', 'reject']:
            return JsonResponse(
                {'message': 'Invalid action.'},
                status=status.HTTP_400_BAD_REQUEST)

        proposal = self.get_proposal(taxonomy_update_proposal_id)
        if not proposal:
            taxon_group = get_object_or_404(TaxonGroup, id=taxon_group_id)
            proposal = self.create_or_find_proposal(taxon_id, taxon_group)

        message = self.handle_action(request, proposal, action)
        return JsonResponse(
            {'message': message}, status=status.HTTP_202_ACCEPTED)

    def create_or_find_proposal(self, taxon_id, taxon_group):
        """
        Creates or finds a taxonomy update proposal based on the taxon and taxon group.

        Parameters:
            taxon_id (int): The ID of the taxon.
            taxon_group (TaxonGroup): The taxon group instance.

        Returns:
            TaxonomyUpdateProposal: The proposal instance.
        """
        all_group_ids = [taxon_group.id] + [group.id for group in taxon_group.get_all_children()]

        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy_id=taxon_id,
            taxon_group_id__in=all_group_ids,
            status='pending'
        ).first()

        if not proposal:
            proposal = create_taxon_proposal(
                taxon=Taxonomy.objects.get(id=taxon_id),
                data={},
                taxon_group=taxon_group,
            )

        return proposal
