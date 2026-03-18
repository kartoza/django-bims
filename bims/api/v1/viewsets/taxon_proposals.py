# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for TaxonomyUpdateProposal in API v1.

Provides endpoints for managing taxon update proposals (add/edit workflow).

Made with love by Kartoza | https://kartoza.com
"""
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanValidate, IsExpertOrSuperuser
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal


class TaxonProposalSerializer:
    """Inline serializer for taxon proposals."""

    @staticmethod
    def serialize(proposal, include_details=False):
        """Serialize a TaxonomyUpdateProposal."""
        data = {
            'id': proposal.id,
            'scientific_name': proposal.scientific_name,
            'canonical_name': proposal.canonical_name,
            'rank': proposal.rank,
            'author': proposal.author,
            'status': proposal.status,
            'new_data': proposal.new_data,
            'created_at': proposal.created_at.isoformat() if proposal.created_at else None,
            'modified_at': proposal.modified_at.isoformat() if proposal.modified_at else None,
            'taxon_group': {
                'id': proposal.taxon_group.id,
                'name': proposal.taxon_group.name,
            } if proposal.taxon_group else None,
            'owner': {
                'id': proposal.owner.id,
                'username': proposal.owner.username,
            } if proposal.owner else None,
        }

        if include_details:
            data.update({
                'taxonomic_status': proposal.taxonomic_status,
                'iucn_status': {
                    'id': proposal.iucn_status.id,
                    'category': proposal.iucn_status.category,
                } if proposal.iucn_status else None,
                'endemism': {
                    'id': proposal.endemism.id,
                    'name': proposal.endemism.name,
                } if proposal.endemism else None,
                'origin': proposal.origin,
                'parent': {
                    'id': proposal.parent.id,
                    'canonical_name': proposal.parent.canonical_name,
                } if proposal.parent else None,
                'accepted_taxonomy': {
                    'id': proposal.accepted_taxonomy.id,
                    'canonical_name': proposal.accepted_taxonomy.canonical_name,
                } if proposal.accepted_taxonomy else None,
                'original_taxonomy': {
                    'id': proposal.original_taxonomy.id,
                    'canonical_name': proposal.original_taxonomy.canonical_name,
                } if proposal.original_taxonomy else None,
                'additional_data': proposal.additional_data,
                'collector_user': {
                    'id': proposal.collector_user.id,
                    'username': proposal.collector_user.username,
                } if proposal.collector_user else None,
            })

        return data


class TaxonProposalViewSet(ModelViewSet):
    """
    ViewSet for TaxonomyUpdateProposal CRUD operations.

    Provides workflow management for taxon additions and updates.

    Endpoints:
    - GET /api/v1/taxon-proposals/ - List proposals
    - POST /api/v1/taxon-proposals/ - Create proposal
    - GET /api/v1/taxon-proposals/{id}/ - Get proposal detail
    - PUT /api/v1/taxon-proposals/{id}/ - Update proposal
    - DELETE /api/v1/taxon-proposals/{id}/ - Delete proposal
    - POST /api/v1/taxon-proposals/{id}/approve/ - Approve proposal
    - POST /api/v1/taxon-proposals/{id}/reject/ - Reject proposal
    - GET /api/v1/taxon-proposals/pending/ - Get pending proposals
    - POST /api/v1/taxon-proposals/bulk-approve/ - Bulk approve proposals
    """

    queryset = TaxonomyUpdateProposal.objects.select_related(
        'taxon_group',
        'owner',
        'original_taxonomy',
        'iucn_status',
        'endemism',
        'parent',
        'accepted_taxonomy',
    ).all()
    permission_classes = [IsAuthenticated]
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()

        # Superusers see all
        if user.is_superuser:
            return queryset.order_by('-created_at')

        # Staff see all too
        if user.is_staff:
            return queryset.order_by('-created_at')

        # Regular users see only their own proposals
        return queryset.filter(owner=user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List proposals with filtering."""
        queryset = self.get_queryset()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        taxon_group = request.query_params.get('taxon_group')
        if taxon_group:
            queryset = queryset.filter(taxon_group_id=taxon_group)

        new_data = request.query_params.get('new_data')
        if new_data:
            queryset = queryset.filter(new_data=new_data.lower() == 'true')

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [TaxonProposalSerializer.serialize(p) for p in page]
            return self.get_paginated_response(data)

        data = [TaxonProposalSerializer.serialize(p) for p in queryset]
        return success_response(data=data)

    def retrieve(self, request, *args, **kwargs):
        """Get proposal details."""
        try:
            proposal = self.get_object()
        except TaxonomyUpdateProposal.DoesNotExist:
            return error_response(
                errors={'detail': 'Proposal not found'},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data = TaxonProposalSerializer.serialize(proposal, include_details=True)
        return success_response(data=data)

    def create(self, request, *args, **kwargs):
        """Create a new taxon proposal."""
        data = request.data

        # Required fields
        required_fields = ['scientific_name', 'canonical_name', 'rank', 'taxon_group']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return validation_error_response({
                'detail': f"Missing required fields: {', '.join(missing)}"
            })

        from bims.models.taxon_group import TaxonGroup

        try:
            taxon_group = TaxonGroup.objects.get(id=data['taxon_group'])
        except TaxonGroup.DoesNotExist:
            return validation_error_response({'taxon_group': 'Invalid taxon group ID'})

        proposal = TaxonomyUpdateProposal(
            scientific_name=data['scientific_name'],
            canonical_name=data['canonical_name'],
            rank=data.get('rank', 'SPECIES'),
            author=data.get('author', ''),
            taxon_group=taxon_group,
            owner=request.user,
            collector_user=request.user,
            new_data=True,
            status='pending',
        )

        # Optional fields
        if data.get('parent'):
            from bims.models.taxonomy import Taxonomy
            try:
                proposal.parent = Taxonomy.objects.get(id=data['parent'])
            except Taxonomy.DoesNotExist:
                pass

        if data.get('taxonomic_status'):
            proposal.taxonomic_status = data['taxonomic_status']

        if data.get('iucn_status'):
            from bims.models import IUCNStatus
            try:
                proposal.iucn_status = IUCNStatus.objects.get(id=data['iucn_status'])
            except IUCNStatus.DoesNotExist:
                pass

        if data.get('endemism'):
            from bims.models import Endemism
            try:
                proposal.endemism = Endemism.objects.get(id=data['endemism'])
            except Endemism.DoesNotExist:
                pass

        if data.get('origin'):
            proposal.origin = data['origin']

        if data.get('additional_data'):
            proposal.additional_data = data['additional_data']

        proposal.save()

        return success_response(
            data=TaxonProposalSerializer.serialize(proposal),
            meta={'created': True},
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], permission_classes=[CanValidate])
    def approve(self, request, pk=None):
        """
        Approve a taxon proposal.

        This applies the proposed changes to the taxonomy.
        """
        try:
            proposal = self.get_object()
        except TaxonomyUpdateProposal.DoesNotExist:
            return error_response(
                errors={'detail': 'Proposal not found'},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if proposal.status == 'approved':
            return error_response(
                errors={'detail': 'Proposal is already approved'},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Use the model's approve method which handles all the logic
            proposal.approve()
            return success_response(
                data=TaxonProposalSerializer.serialize(proposal),
                meta={
                    'approved': True,
                    'taxon_id': proposal.original_taxonomy.id if proposal.original_taxonomy else None,
                },
            )
        except Exception as e:
            return error_response(
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """
        Reject a taxon proposal.
        """
        try:
            proposal = self.get_object()
        except TaxonomyUpdateProposal.DoesNotExist:
            return error_response(
                errors={'detail': 'Proposal not found'},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if proposal.status == 'rejected':
            return error_response(
                errors={'detail': 'Proposal is already rejected'},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        comments = request.data.get('comments', '')

        try:
            # Use the model's reject method
            proposal.reject_data(comments=comments)
            return success_response(
                data=TaxonProposalSerializer.serialize(proposal),
                meta={'rejected': True, 'comments': comments},
            )
        except Exception as e:
            return error_response(
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending proposals for the current user.

        Staff/superusers see all pending proposals.
        Experts see pending proposals for their taxon groups.
        Regular users see their own pending proposals.
        """
        queryset = self.get_queryset().filter(status='pending')

        # Additional filtering for experts
        if not request.user.is_superuser and not request.user.is_staff:
            # Check if user is expert for any groups
            from bims.models.taxon_group import TaxonGroup
            expert_groups = TaxonGroup.objects.filter(experts=request.user)
            if expert_groups.exists():
                queryset = queryset.filter(taxon_group__in=expert_groups)

        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [TaxonProposalSerializer.serialize(p) for p in page]
            return self.get_paginated_response(data)

        data = [TaxonProposalSerializer.serialize(p) for p in queryset]
        return success_response(data=data, meta={'count': len(data)})

    @action(detail=False, methods=['post'], permission_classes=[CanValidate])
    def bulk_approve(self, request):
        """
        Bulk approve proposals.

        Body:
        - proposal_ids: List of proposal IDs to approve (optional, if not provided uses filters)
        - taxon_group: Taxon group ID to approve all pending proposals for
        - include_children: Include proposals for child taxa (default: False)
        """
        proposal_ids = request.data.get('proposal_ids', [])
        taxon_group_id = request.data.get('taxon_group')
        include_children = request.data.get('include_children', False)

        if not proposal_ids and not taxon_group_id:
            return validation_error_response({
                'detail': 'Either proposal_ids or taxon_group is required'
            })

        if proposal_ids:
            proposals = TaxonomyUpdateProposal.objects.filter(
                id__in=proposal_ids,
                status='pending',
            )
        else:
            proposals = TaxonomyUpdateProposal.objects.filter(
                taxon_group_id=taxon_group_id,
                status='pending',
            )

        approved_count = 0
        errors = []

        for proposal in proposals:
            try:
                proposal.approve()
                approved_count += 1
            except Exception as e:
                errors.append({
                    'proposal_id': proposal.id,
                    'error': str(e),
                })

        return success_response(
            data={
                'approved_count': approved_count,
                'error_count': len(errors),
                'errors': errors if errors else None,
            },
            meta={'bulk_approve': True},
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary statistics for proposals.
        """
        queryset = self.get_queryset()

        summary = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'new_taxa': queryset.filter(new_data=True).count(),
            'updates': queryset.filter(new_data=False).count(),
        }

        # By taxon group
        by_group = queryset.filter(status='pending').values(
            'taxon_group__id',
            'taxon_group__name',
        ).annotate(count=Count('id')).order_by('-count')

        summary['by_taxon_group'] = list(by_group)

        return success_response(data=summary)
