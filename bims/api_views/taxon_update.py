from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse, Http404

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import TaxonGroupTaxonomy, IUCNStatus, Endemism
from bims.models.taxonomy import Taxonomy
from bims.models.taxonomy_update_proposal import (
    TaxonomyUpdateProposal
)
from bims.models.taxon_group import TaxonGroup


def create_taxon_proposal(taxon, taxon_group, data={}, iucn_status=None, endemism=None):
    if not iucn_status:
        iucn_status = taxon.iucn_status
    if not endemism:
        endemism = taxon.endemism
    taxonomic_status = (
        data.get('taxonomic_status', 'ACCEPTED')
    )
    if taxonomic_status.lower() == 'accepted':
        accepted_taxonomy = None
    else:
        accepted_taxonomy = (
            data.get('accepted_taxonomy', taxon.accepted_taxonomy),
        )

    proposal, created = TaxonomyUpdateProposal.objects.get_or_create(
        original_taxonomy=taxon,
        taxon_group=taxon_group,
        status='pending',
        defaults={
            'author': data.get('author', taxon.author),
            'rank': data.get('rank', taxon.rank),
            'scientific_name': data.get('scientific_name', taxon.scientific_name),
            'canonical_name': data.get('canonical_name', taxon.canonical_name),
            'origin': data.get('origin', taxon.origin),
            'iucn_status': iucn_status,
            'endemism': endemism,
            'taxon_group_under_review': taxon_group,
            'taxonomic_status': taxonomic_status,
            'accepted_taxonomy': accepted_taxonomy,
            'parent': data.get('parent', taxon.parent),
            'hierarchical_data': taxon.hierarchical_data,
            'gbif_data': taxon.gbif_data,
        }
    )
    if created:
        if data.get('tags'):
            proposal.tags.set(data.get('tags'))
        else:
            proposal.tags.clear()
        if data.get('biographic_distributions'):
            proposal.biographic_distributions.set(data.get('biographic_distributions'))
        else:
            proposal.biographic_distributions.clear()
        proposal.save()

    return proposal


def update_taxon_proposal(
        proposal: TaxonomyUpdateProposal,
        data=None,
        iucn_status=None,
        endemism=None):
    if data is None:
        data = {}
    if not iucn_status:
        iucn_status = proposal.iucn_status
    if not endemism:
        endemism = proposal.endemism
    TaxonomyUpdateProposal.objects.filter(
        id=proposal.id
    ).update(
        status='pending',
        author=data.get('author', proposal.author),
        rank=data.get('rank', proposal.rank),
        scientific_name=data.get(
            'scientific_name', proposal.scientific_name),
        canonical_name=data.get(
            'canonical_name', proposal.canonical_name),
        origin=data.get('origin', proposal.origin),
        iucn_status=iucn_status,
        endemism=endemism,
    )

def is_expert(user, taxon_group):
    if user.is_superuser:
        return True
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
                    endemism=endemism
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
