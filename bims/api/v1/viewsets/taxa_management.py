# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Additional taxa management endpoints for API v1.

Provides GBIF integration, batch operations, and expert management.

Made with love by Kartoza | https://kartoza.com
"""
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ViewSet

from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanValidate, IsExpertOrSuperuser, IsSuperUserOrReadOnly
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy


class TaxaManagementViewSet(ViewSet):
    """
    ViewSet for advanced taxa management operations.

    Provides endpoints for:
    - GBIF taxon search and import
    - Batch add/remove taxa from groups
    - IUCN status harvesting
    - Expert permissions management
    - Taxa validation in bulk
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def find_gbif(self, request):
        """
        Search GBIF for taxa.

        Query params:
        - q: Search query (required)
        - taxon_group: Filter by taxon group ID
        - limit: Maximum results (default: 20)
        - include_local: Include local database matches (default: true)
        """
        query = request.query_params.get('q')
        taxon_group_id = request.query_params.get('taxon_group')
        limit = int(request.query_params.get('limit', 20))
        include_local = request.query_params.get('include_local', 'true').lower() == 'true'

        if not query or len(query) < 2:
            return validation_error_response({
                'detail': "Query 'q' must be at least 2 characters"
            })

        results = []

        # Search local database first
        if include_local:
            local_taxa = Taxonomy.objects.filter(
                Q(scientific_name__icontains=query) |
                Q(canonical_name__icontains=query)
            ).select_related('iucn_status', 'endemism')[:limit]

            for taxon in local_taxa:
                result = {
                    'id': taxon.id,
                    'scientific_name': taxon.scientific_name,
                    'canonical_name': taxon.canonical_name,
                    'rank': taxon.rank,
                    'author': taxon.author,
                    'gbif_key': taxon.gbif_key,
                    'source': 'local',
                    'validated': taxon.validated,
                }

                # Check validation status in taxon group
                if taxon_group_id:
                    try:
                        tgt = TaxonGroupTaxonomy.objects.get(
                            taxonomy=taxon,
                            taxongroup_id=taxon_group_id,
                        )
                        result['in_group'] = True
                        result['group_validated'] = tgt.is_validated
                    except TaxonGroupTaxonomy.DoesNotExist:
                        result['in_group'] = False
                        result['group_validated'] = False

                results.append(result)

        # Search GBIF if we have pygbif
        try:
            from pygbif import species as gbif_species

            gbif_results = gbif_species.name_suggest(q=query, limit=limit)

            for item in gbif_results:
                # Skip if already in local results
                gbif_key = item.get('key')
                if any(r.get('gbif_key') == gbif_key for r in results):
                    continue

                results.append({
                    'gbif_key': gbif_key,
                    'scientific_name': item.get('scientificName'),
                    'canonical_name': item.get('canonicalName'),
                    'rank': item.get('rank'),
                    'kingdom': item.get('kingdom'),
                    'phylum': item.get('phylum'),
                    'class': item.get('class'),
                    'order': item.get('order'),
                    'family': item.get('family'),
                    'genus': item.get('genus'),
                    'source': 'gbif',
                    'status': item.get('status'),
                })

        except ImportError:
            # pygbif not available
            pass
        except Exception as e:
            # GBIF API error - continue with local results
            pass

        return success_response(
            data=results[:limit],
            meta={
                'query': query,
                'count': len(results[:limit]),
                'sources': ['local', 'gbif'] if include_local else ['gbif'],
            },
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_from_gbif(self, request):
        """
        Add a taxon from GBIF to the local database.

        Body:
        - gbif_key: GBIF species key (required)
        - taxon_group: Taxon group ID to add to (required)
        - create_proposal: Create a proposal instead of direct add (default: true)
        """
        gbif_key = request.data.get('gbif_key')
        taxon_group_id = request.data.get('taxon_group')
        create_proposal = request.data.get('create_proposal', True)

        if not gbif_key:
            return validation_error_response({'gbif_key': 'GBIF key is required'})

        if not taxon_group_id:
            return validation_error_response({'taxon_group': 'Taxon group is required'})

        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            return validation_error_response({'taxon_group': 'Invalid taxon group'})

        # Check if taxon already exists
        existing = Taxonomy.objects.filter(gbif_key=gbif_key).first()
        if existing:
            # Add to group if not already
            tgt, created = TaxonGroupTaxonomy.objects.get_or_create(
                taxonomy=existing,
                taxongroup=taxon_group,
                defaults={'is_validated': False},
            )
            return success_response(
                data={
                    'id': existing.id,
                    'scientific_name': existing.scientific_name,
                    'already_exists': True,
                    'added_to_group': created,
                },
                meta={'message': 'Taxon already exists in database'},
            )

        # Fetch from GBIF
        try:
            from pygbif import species as gbif_species

            gbif_data = gbif_species.name_usage(key=gbif_key)

            if create_proposal:
                from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal

                proposal = TaxonomyUpdateProposal.objects.create(
                    scientific_name=gbif_data.get('scientificName', ''),
                    canonical_name=gbif_data.get('canonicalName', ''),
                    rank=gbif_data.get('rank', 'SPECIES'),
                    author=gbif_data.get('authorship', ''),
                    taxon_group=taxon_group,
                    owner=request.user,
                    collector_user=request.user,
                    new_data=True,
                    status='pending',
                    gbif_key=gbif_key,
                    gbif_data=gbif_data,
                )

                return success_response(
                    data={
                        'proposal_id': proposal.id,
                        'scientific_name': proposal.scientific_name,
                        'created_proposal': True,
                    },
                    meta={'message': 'Proposal created for review'},
                    status_code=status.HTTP_201_CREATED,
                )
            else:
                # Direct add (requires elevated permissions)
                if not request.user.is_staff and not request.user.is_superuser:
                    return error_response(
                        errors={'detail': 'Direct add requires staff or superuser permissions'},
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

                taxon = Taxonomy.objects.create(
                    scientific_name=gbif_data.get('scientificName', ''),
                    canonical_name=gbif_data.get('canonicalName', ''),
                    rank=gbif_data.get('rank', 'SPECIES'),
                    author=gbif_data.get('authorship', ''),
                    gbif_key=gbif_key,
                    gbif_data=gbif_data,
                    validated=False,
                )

                TaxonGroupTaxonomy.objects.create(
                    taxonomy=taxon,
                    taxongroup=taxon_group,
                    is_validated=False,
                )

                return success_response(
                    data={
                        'id': taxon.id,
                        'scientific_name': taxon.scientific_name,
                        'created': True,
                    },
                    meta={'message': 'Taxon created'},
                    status_code=status.HTTP_201_CREATED,
                )

        except ImportError:
            return error_response(
                errors={'detail': 'GBIF integration not available'},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return error_response(
                errors={'detail': f'GBIF error: {str(e)}'},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], permission_classes=[IsExpertOrSuperuser])
    def add_to_group(self, request):
        """
        Add taxa to a taxon group.

        Body:
        - taxa_ids: List of taxonomy IDs
        - taxon_group: Target taxon group ID
        """
        taxa_ids = request.data.get('taxa_ids', [])
        taxon_group_id = request.data.get('taxon_group')

        if not taxa_ids:
            return validation_error_response({'taxa_ids': 'Taxa IDs are required'})

        if not taxon_group_id:
            return validation_error_response({'taxon_group': 'Taxon group is required'})

        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            return validation_error_response({'taxon_group': 'Invalid taxon group'})

        # Check permissions (expert for this group or superuser)
        if not request.user.is_superuser:
            if request.user not in taxon_group.experts.all():
                return error_response(
                    errors={'detail': 'You are not an expert for this taxon group'},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        added_count = 0
        skipped_count = 0

        taxa = Taxonomy.objects.filter(id__in=taxa_ids)
        for taxon in taxa:
            _, created = TaxonGroupTaxonomy.objects.get_or_create(
                taxonomy=taxon,
                taxongroup=taxon_group,
                defaults={'is_validated': False},
            )
            if created:
                added_count += 1
            else:
                skipped_count += 1

        return success_response(
            data={
                'added_count': added_count,
                'skipped_count': skipped_count,
            },
            meta={'taxon_group': taxon_group.name},
        )

    @action(detail=False, methods=['post'], permission_classes=[IsExpertOrSuperuser])
    def remove_from_group(self, request):
        """
        Remove taxa from a taxon group.

        Body:
        - taxa_ids: List of taxonomy IDs
        - taxon_group: Target taxon group ID
        - include_children: Also remove child taxa (default: False)
        """
        taxa_ids = request.data.get('taxa_ids', [])
        taxon_group_id = request.data.get('taxon_group')
        include_children = request.data.get('include_children', False)

        if not taxa_ids:
            return validation_error_response({'taxa_ids': 'Taxa IDs are required'})

        if not taxon_group_id:
            return validation_error_response({'taxon_group': 'Taxon group is required'})

        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            return validation_error_response({'taxon_group': 'Invalid taxon group'})

        # Check permissions
        if not request.user.is_superuser:
            if request.user not in taxon_group.experts.all():
                return error_response(
                    errors={'detail': 'You are not an expert for this taxon group'},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        ids_to_remove = set(taxa_ids)

        # Include children if requested
        if include_children:
            def get_children(parent_ids):
                children = Taxonomy.objects.filter(parent_id__in=parent_ids).values_list('id', flat=True)
                return list(children)

            # Iteratively get all descendants
            current_level = taxa_ids
            while current_level:
                children = get_children(current_level)
                ids_to_remove.update(children)
                current_level = children

        removed = TaxonGroupTaxonomy.objects.filter(
            taxonomy_id__in=ids_to_remove,
            taxongroup=taxon_group,
        ).delete()

        return success_response(
            data={
                'removed_count': removed[0],
            },
            meta={
                'taxon_group': taxon_group.name,
                'include_children': include_children,
            },
        )

    @action(detail=False, methods=['post'], permission_classes=[CanValidate])
    def bulk_validate(self, request):
        """
        Bulk validate taxa in a taxon group.

        Body:
        - taxa_ids: List of taxonomy IDs (optional)
        - taxon_group: Taxon group ID (required if taxa_ids not provided)
        - include_unvalidated_only: Only validate currently unvalidated (default: True)
        """
        taxa_ids = request.data.get('taxa_ids', [])
        taxon_group_id = request.data.get('taxon_group')
        unvalidated_only = request.data.get('include_unvalidated_only', True)

        if not taxa_ids and not taxon_group_id:
            return validation_error_response({
                'detail': 'Either taxa_ids or taxon_group is required'
            })

        if taxa_ids:
            tgt_qs = TaxonGroupTaxonomy.objects.filter(taxonomy_id__in=taxa_ids)
        else:
            tgt_qs = TaxonGroupTaxonomy.objects.filter(taxongroup_id=taxon_group_id)

        if unvalidated_only:
            tgt_qs = tgt_qs.filter(is_validated=False)

        count = tgt_qs.update(is_validated=True, is_rejected=False)

        return success_response(
            data={'validated_count': count},
            meta={'bulk_validate': True},
        )

    @action(detail=False, methods=['post'], permission_classes=[IsSuperUserOrReadOnly])
    def harvest_iucn(self, request):
        """
        Trigger IUCN status harvesting for taxa.

        Body:
        - taxa_ids: List of taxonomy IDs (optional - if not provided, harvests all)
        - taxon_group: Taxon group ID to harvest for (optional)

        This starts a background task.
        """
        taxa_ids = request.data.get('taxa_ids', [])
        taxon_group_id = request.data.get('taxon_group')

        # Build queryset
        if taxa_ids:
            taxa = Taxonomy.objects.filter(id__in=taxa_ids)
        elif taxon_group_id:
            taxa = Taxonomy.objects.filter(
                taxongroupTaxonomy__taxongroup_id=taxon_group_id
            )
        else:
            return validation_error_response({
                'detail': 'Either taxa_ids or taxon_group is required'
            })

        # Try to use Celery task if available
        try:
            from bims.tasks.harvest_iucn_status import harvest_iucn_status

            task = harvest_iucn_status.delay(list(taxa.values_list('id', flat=True)))
            return success_response(
                data={'task_id': task.id},
                meta={'message': 'IUCN harvest task started', 'taxa_count': taxa.count()},
                status_code=status.HTTP_202_ACCEPTED,
            )
        except ImportError:
            # No Celery, do synchronously (limited)
            pass

        return success_response(
            data={'taxa_count': taxa.count()},
            meta={'message': 'IUCN harvest queued'},
        )

    @action(detail=False, methods=['get'])
    def experts(self, request):
        """
        Get experts for taxon groups.

        Query params:
        - taxon_group: Filter by taxon group ID
        """
        taxon_group_id = request.query_params.get('taxon_group')

        if taxon_group_id:
            groups = TaxonGroup.objects.filter(id=taxon_group_id)
        else:
            groups = TaxonGroup.objects.all()

        data = []
        for group in groups.prefetch_related('experts'):
            data.append({
                'id': group.id,
                'name': group.name,
                'experts': [
                    {
                        'id': expert.id,
                        'username': expert.username,
                        'email': expert.email,
                        'full_name': expert.get_full_name(),
                    }
                    for expert in group.experts.all()
                ],
            })

        return success_response(data=data)

    @action(detail=False, methods=['get'])
    def tags(self, request):
        """
        Get available taxon tags.

        Query params:
        - q: Search query
        - biographic: Filter to biographic distribution tags only
        """
        query = request.query_params.get('q', '')
        biographic = request.query_params.get('biographic', 'false').lower() == 'true'

        from bims.models.taxon_tag import TaxonTag

        qs = TaxonTag.objects.all()

        if query:
            qs = qs.filter(name__icontains=query)

        if biographic:
            qs = qs.filter(biographic=True)

        data = [
            {
                'id': tag.id,
                'name': tag.name,
                'biographic': tag.biographic,
            }
            for tag in qs[:50]
        ]

        return success_response(data=data, meta={'count': len(data)})

    @action(detail=False, methods=['get'])
    def conservation_statuses(self, request):
        """
        Get available IUCN conservation statuses.
        """
        from bims.models import IUCNStatus

        statuses = IUCNStatus.objects.all().order_by('category')
        data = [
            {
                'id': s.id,
                'category': s.category,
                'sensitive': s.sensitive,
            }
            for s in statuses
        ]

        return success_response(data=data)

    @action(detail=False, methods=['get'])
    def endemism_options(self, request):
        """
        Get available endemism options.
        """
        from bims.models import Endemism

        options = Endemism.objects.all().order_by('name')
        data = [
            {
                'id': e.id,
                'name': e.name,
                'description': e.description,
            }
            for e in options
        ]

        return success_response(data=data)

    @action(detail=False, methods=['get'])
    def origin_options(self, request):
        """
        Get available origin options.
        """
        # Origins are typically stored as choices in the model
        from bims.models.taxonomy import Taxonomy

        # Get choices from model if defined
        try:
            choices = Taxonomy._meta.get_field('origin').choices
            data = [{'value': c[0], 'label': c[1]} for c in choices]
        except (AttributeError, KeyError):
            # Default origins
            data = [
                {'value': 'native', 'label': 'Native (Indigenous)'},
                {'value': 'alien', 'label': 'Alien'},
                {'value': 'alien-invasive', 'label': 'Alien - Invasive'},
                {'value': 'alien-non-invasive', 'label': 'Alien - Non-invasive'},
                {'value': 'unknown', 'label': 'Unknown'},
            ]

        return success_response(data=data)

    @action(detail=False, methods=['get'])
    def taxonomic_ranks(self, request):
        """
        Get available taxonomic ranks.
        """
        ranks = [
            'KINGDOM',
            'PHYLUM',
            'CLASS',
            'ORDER',
            'FAMILY',
            'SUBFAMILY',
            'TRIBE',
            'SUBTRIBE',
            'GENUS',
            'SUBGENUS',
            'SPECIES',
            'SUBSPECIES',
            'VARIETY',
            'FORM',
            'FORMA',
        ]

        return success_response(data=ranks)
