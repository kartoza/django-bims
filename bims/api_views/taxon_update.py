from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse, Http404

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.taxonomy import Taxonomy
from bims.models.taxonomy_update_proposal import (
    TaxonomyUpdateProposal
)
from bims.models.taxon_group import TaxonGroup


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
        # Check if taxon is still being edited
        if self.is_taxon_edited(taxon):
            return Response({
                'message': 'Taxon is still being edited'
            }, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        with transaction.atomic():
            proposal = TaxonomyUpdateProposal.objects.create(
                original_taxonomy=taxon,
                taxon_group=taxon_group,
                status='pending',
                scientific_name=data.get(
                    'scientific_name', taxon.scientific_name),
                canonical_name=data.get(
                    'canonical_name', taxon.canonical_name)
            )

        return Response(
            {
                'message': 'Taxonomy update proposal created successfully',
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
        Superusers can review any proposal,
        while other users must be experts of the taxon group.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        user = self.request.user
        if user.is_superuser:
            return True

        proposal_id = self.kwargs.get('taxonomy_update_proposal_id', None)
        if proposal_id:
            proposal = get_object_or_404(TaxonomyUpdateProposal, pk=proposal_id)
            if not proposal.taxon_group:
                return False
            taxon_group = proposal.taxon_group
        else:
            taxon_id = self.kwargs.get('taxon_id')
            taxon_group_id = self.kwargs.get('taxon_group_id')
            proposal, _ = TaxonomyUpdateProposal.objects.update_or_create(
                original_taxonomy_id=taxon_id,
                taxon_group_id=taxon_group_id,
                defaults={
                    'status': 'pending'
                }
            )
            taxon_group = proposal.taxon_group

        experts = taxon_group.get_all_experts()
        return user in experts

    def handle_proposal(self, request, proposal_id, action) -> JsonResponse:
        """
        Handles the approval or rejection of a taxonomy update
        proposal based on the specified action.

        Parameters:
            request (HttpRequest): The request object.
            proposal_id (int): The ID of the taxonomy update proposal.
            action (str): The action to perform ('approve' or 'reject').

        Returns:
            JsonResponse: A response with the outcome message and HTTP status.
        """
        proposal = get_object_or_404(TaxonomyUpdateProposal, pk=proposal_id)
        if action == 'approve':
            proposal.approve(request.user)
            message = 'Taxonomy update proposal approved successfully'
        else:
            comments = request.data.get('comments', '')
            proposal.reject_data(request.user, comments)
            message = 'Taxonomy update proposal rejected successfully'
        return JsonResponse(
            {'message': message},
            status=status.HTTP_202_ACCEPTED)

    def handle_taxon_review(self, request, taxon_id, taxon_group_id, action) -> JsonResponse:
        """
        Handles the approval or rejection of a taxonomy update
        proposal based on the specified action.

        Parameters:
            request (HttpRequest): The request object.
            taxon_id (int): The ID of the taxon
            taxon_group_id (int,): The ID of the taxon group
            action (str): The action to perform ('approve' or 'reject').

        Returns:
            JsonResponse: A response with the outcome message and HTTP status.
        """
        try:
            proposal = TaxonomyUpdateProposal.objects.get(
                original_taxonomy_id=taxon_id,
                taxon_group_id=taxon_group_id
            )
        except TaxonomyUpdateProposal.DoesNotExist:
            raise Http404()
        if action == 'approve':
            proposal.approve(request.user)
            message = 'Taxonomy update proposal approved successfully'
        else:
            comments = request.data.get('comments', '')
            proposal.reject_data(request.user, comments)
            message = 'Taxonomy update proposal rejected successfully'
        return JsonResponse(
            {'message': message},
            status=status.HTTP_202_ACCEPTED)

    def put(self, request, taxonomy_update_proposal_id=None, taxon_id=None, taxon_group_id=None) -> JsonResponse:
        """
        Handles PUT requests to update the status of a taxonomy update proposal.

        Parameters:
            request (HttpRequest): The request object.
            taxonomy_update_proposal_id (int): The ID of the taxonomy update proposal.
            taxon_id (int, optional): The ID of the taxon, if provided.
            taxon_group_id (int, optional): The ID of the taxon group, if provided.
        Returns:
            JsonResponse: A response with the outcome message and HTTP status.
        """
        new_status = request.data.get('action')
        if new_status not in ['approve', 'reject']:
            return JsonResponse(
                {'message': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST)

        if taxon_id is not None and taxon_group_id is not None:
            # Process the review for the specific taxon and taxon group
            # You might need to add a new method or logic here to handle this case
            return self.handle_taxon_review(
                request, taxon_id, taxon_group_id, new_status
            )
        else:
            # Process the proposal review as before
            return self.handle_proposal(
                request, taxonomy_update_proposal_id, new_status
            )
