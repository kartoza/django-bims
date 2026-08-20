# coding=utf-8
import ast

from braces.views import SuperuserRequiredMixin
from django.db.models import F, IntegerField, Q
from django.db.models.fields.related import ForeignObjectRel
from django.utils import timezone
from django.views.generic import TemplateView

from preferences import preferences
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.models.upstream_deletion_check import (
    DataUpstreamDeletionCheckResult,
    DataUpstreamDeletionCheckSession,
)
from bims.models.taxon_group import TaxonGroup
from bims.models.taxonomy import Taxonomy
from bims.utils.gbif import find_species
from bims.utils.iucn import get_global_iucn_status, get_iucn_status

TOP_LEVEL_RANKS = {'DOMAIN', 'KINGDOM'}

CHECKS = [
    {
        'key': 'missing_parent',
        'label': 'Missing parent',
        'description': (
            'Accepted or doubtful taxa below kingdom/domain rank '
            'that have no parent taxon.'
        ),
    },
    {
        'key': 'synonym_no_accepted',
        'label': 'Synonym without accepted taxon',
        'description': (
            'Taxa whose taxonomic status contains "synonym" but whose '
            'accepted_taxonomy field is empty.'
        ),
    },
    {
        'key': 'accepted_is_synonym',
        'label': 'Accepted taxon is itself a synonym',
        'description': (
            'Synonyms whose accepted_taxonomy is also marked as a synonym '
            'instead of an accepted taxon.'
        ),
    },
    {
        'key': 'subspecies_synonym_parent',
        'label': 'Subspecies / variety with synonym parent',
        'description': (
            'Non-synonym subspecies or varieties whose direct parent taxon '
            'is a synonym.'
        ),
    },
    {
        'key': 'invalid_parent_rank',
        'label': 'Invalid parent rank',
        'description': (
            'Taxa where the parent rank is equal to or lower than the '
            'child rank, or where a taxon is its own parent.'
        ),
    },
    {
        'key': 'duplicate_canonical',
        'label': 'Duplicate canonical names',
        'description': (
            'Taxa that share the same canonical_name and rank as another '
            'taxon in this group.'
        ),
    },
    {
        'key': 'missing_external_id',
        'label': 'Missing external ID',
        'description': (
            'Taxa with no CoL ID, no FADA ID, no Aphia ID, and no '
            'TaxonWorks ID. Taxa from readonly BIMS-harvested groups '
            'are excluded.'
        ),
    },
    {
        'key': 'missing_iucn_global',
        'label': 'Missing IUCN global status',
        'description': (
            'Accepted or doubtful species/subspecies with no Global Red '
            'List (IUCN) status set, or whose status is "Not Evaluated".'
        ),
    },
]


def query_taxa(taxon_group_id=None):
    return (
        Taxonomy.objects.all() if not taxon_group_id else
        Taxonomy.objects.filter(taxongroup__id=taxon_group_id)
    )


def _qs_missing_parent(qs):
    return qs.filter(
        Q(taxonomic_status='ACCEPTED') | Q(taxonomic_status='DOUBTFUL'),
        parent__isnull=True,
    ).exclude(rank__in=TOP_LEVEL_RANKS)


def _qs_synonym_no_accepted(qs):
    return qs.filter(
        taxonomic_status__icontains='SYNONYM',
        accepted_taxonomy__isnull=True,
    )


def _qs_accepted_is_synonym(qs):
    return qs.filter(
        taxonomic_status__icontains='SYNONYM',
        accepted_taxonomy__taxonomic_status__icontains='SYNONYM',
    )


def _qs_subspecies_synonym_parent(qs):
    return qs.filter(
        rank__in=['SUBSPECIES', 'VARIETY'],
        parent__taxonomic_status__icontains='SYNONYM',
    ).exclude(taxonomic_status__icontains='SYNONYM')


def _qs_invalid_parent_rank(qs):
    hierarchy = [rank.name for rank in TaxonomicRank.hierarchy()]
    from django.db.models import Case, When
    rank_whens = [When(rank=r, then=i) for i, r in enumerate(hierarchy)]
    parent_rank_whens = [When(parent__rank=r, then=i) for i, r in enumerate(hierarchy)]

    return qs.filter(parent__isnull=False).annotate(
        rank_order=Case(*rank_whens, default=None, output_field=IntegerField()),
        parent_rank_order=Case(*parent_rank_whens, default=None, output_field=IntegerField()),
    ).filter(
        Q(parent_id=F('id')) |
        Q(
            rank_order__isnull=False,
            parent_rank_order__isnull=False,
            parent_rank_order__gte=F('rank_order'),
        )
    )


def _qs_duplicate_canonical(qs):
    from django.db.models import Count
    duplicated = (
        qs.values('canonical_name', 'rank')
        .annotate(cnt=Count('id'))
        .filter(cnt__gt=1)
        .values_list('canonical_name', flat=True)
    )
    return qs.filter(canonical_name__in=list(duplicated))


def _qs_missing_external_id(qs):
    # Taxa belonging to a readonly (BIMS-harvested) group may legitimately
    # have no CoL/FADA/Aphia/TaxonWorks ID, so exclude them.
    bims_harvested_ids = (
        TaxonGroup.objects
        .filter(is_readonly=True, upstream_url__gt='')
        .values_list('taxonomies__id', flat=True)
    )
    return qs.filter(
        aphia_id__isnull=True,
        taxonworks_id__isnull=True,
    ).filter(
        Q(fada_id__isnull=True) | Q(fada_id='')
    ).filter(
        Q(col_id__isnull=True) | Q(col_id='')
    ).exclude(id__in=bims_harvested_ids)


def _qs_missing_iucn_global(qs):
    # Only accepted/doubtful species and subspecies are expected to carry a
    # Global Red List assessment; synonyms and higher ranks are excluded.
    return qs.filter(
        Q(taxonomic_status='ACCEPTED') | Q(taxonomic_status='DOUBTFUL'),
        rank__in=['SPECIES', 'SUBSPECIES'],
    ).filter(
        Q(iucn_status__isnull=True) | Q(iucn_status__category='NE')
    )


_CHECK_FN = {
    'missing_parent': _qs_missing_parent,
    'synonym_no_accepted': _qs_synonym_no_accepted,
    'accepted_is_synonym': _qs_accepted_is_synonym,
    'subspecies_synonym_parent': _qs_subspecies_synonym_parent,
    'invalid_parent_rank': _qs_invalid_parent_rank,
    'duplicate_canonical': _qs_duplicate_canonical,
    'missing_external_id': _qs_missing_external_id,
    'missing_iucn_global': _qs_missing_iucn_global,
}


def run_checks(taxon_group_id=None):
    base = query_taxa(taxon_group_id)
    return {
        check['key']: _CHECK_FN[check['key']](base).count()
        for check in CHECKS
    }


def taxa_for_check(check_key, taxon_group_id=None, offset=0, limit=50):
    base = query_taxa(taxon_group_id)
    fn = _CHECK_FN.get(check_key)
    if fn is None:
        return [], 0
    qs = fn(base).select_related('parent', 'accepted_taxonomy').order_by('canonical_name')
    total = qs.count()
    page = qs[offset: offset + limit]
    rows = []
    for t in page:
        rows.append({
            'id': t.id,
            'canonical_name': t.canonical_name or '',
            'col_id': t.col_id or '',
            'rank': t.rank or '',
            'taxonomic_status': t.taxonomic_status or '',
            'parent': t.parent.canonical_name if t.parent else '',
            'parent_rank': t.parent.rank if t.parent else '',
            'accepted_taxonomy': (
                t.accepted_taxonomy.canonical_name if t.accepted_taxonomy else ''
            ),
            'accepted_taxonomy_status': (
                t.accepted_taxonomy.taxonomic_status if t.accepted_taxonomy else ''
            ),
        })
    return rows, total


class TaxaValidationView(SuperuserRequiredMixin, TemplateView):
    template_name = 'taxa_validation.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        taxon_group_id = self.request.GET.get('taxonGroup')
        counts = run_checks(taxon_group_id)
        # Build a list of (check_meta, count) so the template can iterate
        # without needing dict-key subscript with a variable.
        ctx['checks_with_counts'] = [
            (check, counts.get(check['key'], 0))
            for check in CHECKS
        ]
        ctx['checks_data'] = CHECKS
        ctx['taxon_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE',
            parent__isnull=True,
        ).order_by('name')
        ctx['selected_group_id'] = taxon_group_id or ''
        ctx['col_check_session'] = DataUpstreamDeletionCheckSession.objects.filter(
            taxon_group_id=taxon_group_id or None,
        ).order_by('-created_at').first()
        return ctx


class TaxaValidationResultsView(SuperuserRequiredMixin, APIView):
    """GET: paginated rows for a given validation check."""

    def get(self, request):
        check_key = request.query_params.get('check', '')
        taxon_group_id = request.query_params.get('taxonGroup') or None
        try:
            offset = int(request.query_params.get('offset', 0))
            limit = int(request.query_params.get('limit', 50))
            limit = min(limit, 200)
        except (TypeError, ValueError):
            offset, limit = 0, 50

        if check_key not in _CHECK_FN:
            return Response(
                {'error': 'Unknown check key'},
                status=status.HTTP_400_BAD_REQUEST)

        rows, total = taxa_for_check(check_key, taxon_group_id, offset, limit)
        return Response({'total': total, 'offset': offset, 'results': rows})


class TaxaAssignGbifKeyView(SuperuserRequiredMixin, APIView):
    """POST: assign a GBIF key to a taxon from the validation page."""

    def post(self, request):
        try:
            taxon_id = int(request.data['taxon_id'])
            gbif_key = int(request.data['gbif_key'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'taxon_id and gbif_key (integers) are required'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        if Taxonomy.objects.filter(gbif_key=gbif_key).exclude(pk=taxon_id).exists():
            return Response(
                {'error': f'GBIF key {gbif_key} is already used by another taxon'},
                status=status.HTTP_409_CONFLICT,
            )

        taxon.gbif_key = gbif_key
        taxon.save(update_fields=['gbif_key'])
        return Response({'ok': True, 'taxon_id': taxon_id, 'gbif_key': gbif_key})


class TaxaAssignParentView(SuperuserRequiredMixin, APIView):
    """POST: assign a parent taxon to a taxon from the validation page."""

    def post(self, request):
        try:
            taxon_id = int(request.data['taxon_id'])
            parent_id = int(request.data['parent_id'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'taxon_id and parent_id (integers) are required'},
                status=status.HTTP_400_BAD_REQUEST)

        if taxon_id == parent_id:
            return Response(
                {'error': 'A taxon cannot be its own parent'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            parent = Taxonomy.objects.get(pk=parent_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Parent taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        taxon.parent = parent
        taxon.save(update_fields=['parent'])
        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'parent_id': parent_id,
            'parent_name': parent.canonical_name or '',
            'parent_rank': parent.rank or '',
        })


class TaxaAssignAcceptedView(SuperuserRequiredMixin, APIView):
    """POST: assign an accepted taxon to a synonym from the validation page."""

    def post(self, request):
        try:
            taxon_id = int(request.data['taxon_id'])
            accepted_id = int(request.data['accepted_id'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'taxon_id and accepted_id (integers) are required'},
                status=status.HTTP_400_BAD_REQUEST)

        if taxon_id == accepted_id:
            return Response(
                {'error': 'A taxon cannot be its own accepted taxon'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            accepted = Taxonomy.objects.get(pk=accepted_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Accepted taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        taxon.accepted_taxonomy = accepted
        taxon.save(update_fields=['accepted_taxonomy'])
        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'accepted_id': accepted_id,
            'accepted_name': accepted.canonical_name or '',
            'accepted_status': accepted.taxonomic_status or '',
        })


def _normalise_gbif_status(raw_status):
    try:
        return TaxonomicStatus[(raw_status or '').upper()].name
    except KeyError:
        return (raw_status or '').upper()


def _clean_col_data(col_data):
    """Strip diagnostics/additionalStatus before persisting to gbif_data."""
    if not col_data:
        return col_data
    return {k: v for k, v in col_data.items() if k not in ('diagnostics', 'additionalStatus')}


def _resolve_or_fetch_by_col_id(col_id):
    if not col_id:
        return None
    taxon = Taxonomy.objects.filter(col_id=col_id).first()
    if taxon:
        return taxon
    from bims.utils.fetch_gbif import fetch_all_species_from_gbif
    return fetch_all_species_from_gbif(
        col_id=col_id,
        fetch_children=False,
        fetch_vernacular_names=False,
    )


class TaxaGbifLookupView(SuperuserRequiredMixin, APIView):
    """GET: look up a taxon on GBIF's Catalogue of Life checklist and
    return a comparison of the current local data vs the COL match, so
    the validation page can preview a fix before applying it."""

    def get(self, request, taxon_id):
        try:
            taxon = Taxonomy.objects.select_related(
                'parent', 'accepted_taxonomy').get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        name = taxon.canonical_name or taxon.scientific_name
        if not name:
            return Response(
                {'error': 'Taxon has no name to search with'},
                status=status.HTTP_400_BAD_REQUEST)

        original = {
            'canonical_name': taxon.canonical_name or '',
            'scientific_name': taxon.scientific_name or '',
            'rank': taxon.rank or '',
            'taxonomic_status': taxon.taxonomic_status or '',
            'col_id': taxon.col_id or '',
            'author': taxon.author or '',
            'parent': taxon.parent.canonical_name if taxon.parent else '',
            'parent_rank': taxon.parent.rank if taxon.parent else '',
            'accepted_taxonomy': (
                taxon.accepted_taxonomy.canonical_name if taxon.accepted_taxonomy else ''
            ),
            'is_synonym': taxon.is_synonym,
        }

        classifier = {}
        kingdom = taxon.kingdom_name
        if kingdom:
            classifier['kingdom'] = kingdom

        col_data = find_species(name, require_exact_match=False, **classifier)

        if not col_data or 'usage' not in col_data:
            return Response({
                'ok': True,
                'taxon_id': taxon_id,
                'original': original,
                'gbif': None,
            })

        usage = col_data.get('usage', {})
        classification = col_data.get('classification', [])
        parent_entry = None
        if len(classification) > 1:
            parent_entry = list(reversed(classification))[1]

        gbif_status = (usage.get('status') or '').upper()
        is_synonym = 'SYNONYM' in gbif_status
        accepted_usage = col_data.get('acceptedUsage') or {}

        proposed = {
            'canonical_name': usage.get('canonicalName', '') or '',
            'scientific_name': usage.get('name', '') or '',
            'rank': (usage.get('rank') or '').upper(),
            'taxonomic_status': _normalise_gbif_status(usage.get('status', '')),
            'col_id': str(usage.get('key') or ''),
            'author': usage.get('authorship', '') or '',
            'parent': parent_entry.get('name', '') if parent_entry else '',
            'parent_rank': (parent_entry.get('rank') or '').upper() if parent_entry else '',
            'parent_col_id': str(parent_entry.get('key') or '') if parent_entry else '',
            'accepted_taxonomy': (
                accepted_usage.get('canonicalName', '') or accepted_usage.get('name', '') or ''
            ) if is_synonym else '',
            'accepted_col_id': (
                str(accepted_usage.get('key') or '') if is_synonym else ''
            ),
            'is_synonym': is_synonym,
            'raw_gbif_data': _clean_col_data(col_data),
        }

        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'original': original,
            'gbif': proposed,
        })


class TaxaApplyGbifFixView(SuperuserRequiredMixin, APIView):
    """POST: apply a previously-fetched COL/GBIF match to a taxon."""

    def post(self, request):
        try:
            taxon_id = int(request.data['taxon_id'])
            gbif = request.data['gbif']
            if not isinstance(gbif, dict):
                raise TypeError
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'taxon_id and gbif payload are required'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        canonical_name = (gbif.get('canonical_name') or '').strip()
        scientific_name = (gbif.get('scientific_name') or '').strip()
        rank = (gbif.get('rank') or '').strip().upper()
        taxonomic_status = (gbif.get('taxonomic_status') or '').strip().upper()
        col_id = (gbif.get('col_id') or '').strip()
        author = (gbif.get('author') or '').strip()
        parent_col_id = (gbif.get('parent_col_id') or '').strip()
        accepted_col_id = (gbif.get('accepted_col_id') or '').strip()
        is_synonym = bool(gbif.get('is_synonym'))

        if col_id and Taxonomy.objects.filter(col_id=col_id).exclude(pk=taxon_id).exists():
            return Response(
                {'error': f'CoL ID {col_id} is already used by another taxon'},
                status=status.HTTP_409_CONFLICT,
            )

        update_fields = []

        if canonical_name and taxon.canonical_name != canonical_name:
            taxon.canonical_name = canonical_name
            update_fields.append('canonical_name')
        if scientific_name and taxon.scientific_name != scientific_name:
            taxon.scientific_name = scientific_name
            update_fields.append('scientific_name')
        if rank and taxon.rank != rank:
            taxon.rank = rank
            update_fields.append('rank')
        if taxonomic_status and taxon.taxonomic_status != taxonomic_status:
            taxon.taxonomic_status = taxonomic_status
            update_fields.append('taxonomic_status')
        if col_id and taxon.col_id != col_id:
            taxon.col_id = col_id
            update_fields.append('col_id')
        if author and taxon.author != author:
            taxon.author = author
            update_fields.append('author')

        raw_gbif_data = gbif.get('raw_gbif_data')
        if isinstance(raw_gbif_data, dict) and raw_gbif_data and taxon.gbif_data != raw_gbif_data:
            taxon.gbif_data = raw_gbif_data
            update_fields.append('gbif_data')

        if is_synonym:
            if accepted_col_id and accepted_col_id != taxon.col_id:
                accepted = _resolve_or_fetch_by_col_id(accepted_col_id)
                if accepted and taxon.accepted_taxonomy_id != accepted.id:
                    taxon.accepted_taxonomy = accepted
                    update_fields.append('accepted_taxonomy')
        elif parent_col_id and parent_col_id != taxon.col_id:
            parent = _resolve_or_fetch_by_col_id(parent_col_id)
            if parent and taxon.parent_id != parent.id:
                taxon.parent = parent
                update_fields.append('parent')

        if update_fields:
            taxon.save(update_fields=update_fields)

        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'updated_fields': update_fields,
        })


def _related_record_summary(taxon):
    """Count records that a merge would reassign away from this taxon,
    mirroring the relations merge_taxa_data() actually touches."""
    links = [
        rel.get_accessor_name() for rel in taxon._meta.get_fields()
        if issubclass(type(rel), ForeignObjectRel)
    ]
    total = 0
    for link in links:
        if link in ('taxongrouptaxonomy_set', 'taxongroup_set'):
            continue
        try:
            total += getattr(taxon, link).count()
        except Exception:
            continue
    return {
        'related_records': total,
        'taxon_groups': taxon.taxongroup_set.count(),
        'vernacular_names': taxon.vernacular_names.count(),
    }


class TaxaDuplicateGroupView(SuperuserRequiredMixin, APIView):
    """GET: list every taxon sharing the same canonical_name + rank as the
    given taxon, with related-record counts, for the merge-duplicates UI."""

    def get(self, request, taxon_id):
        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        group_qs = Taxonomy.objects.filter(
            canonical_name=taxon.canonical_name,
            rank=taxon.rank,
        ).select_related('parent').order_by('id')

        members = []
        for t in group_qs:
            summary = _related_record_summary(t)
            members.append({
                'id': t.id,
                'canonical_name': t.canonical_name or '',
                'scientific_name': t.scientific_name or '',
                'rank': t.rank or '',
                'taxonomic_status': t.taxonomic_status or '',
                'col_id': t.col_id or '',
                'gbif_key': t.gbif_key,
                'parent': t.parent.canonical_name if t.parent else '',
                'related_records': summary['related_records'],
                'taxon_groups': summary['taxon_groups'],
                'vernacular_names': summary['vernacular_names'],
            })

        return Response({
            'ok': True,
            'canonical_name': taxon.canonical_name or '',
            'rank': taxon.rank or '',
            'members': members,
        })


class TaxaMergeDuplicatesView(SuperuserRequiredMixin, APIView):
    """POST: merge a group of duplicate taxa into a single survivor,
    reassigning related records and deleting the rest."""

    def post(self, request):
        try:
            survivor_id = int(request.data['survivor_id'])
            duplicate_ids = [int(i) for i in request.data['duplicate_ids']]
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'survivor_id and duplicate_ids (integers) are required'},
                status=status.HTTP_400_BAD_REQUEST)

        duplicate_ids = [i for i in duplicate_ids if i != survivor_id]
        if not duplicate_ids:
            return Response(
                {'error': 'No duplicate taxa to merge'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            survivor = Taxonomy.objects.get(pk=survivor_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Survivor taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        duplicates = Taxonomy.objects.filter(id__in=duplicate_ids)
        missing = set(duplicate_ids) - set(duplicates.values_list('id', flat=True))
        if missing:
            return Response(
                {'error': f'Taxa not found: {sorted(missing)}'},
                status=status.HTTP_404_NOT_FOUND)

        # Guard against merging taxa that don't actually share the survivor's
        # canonical name/rank - avoids accidental cross-group merges.
        if duplicates.exclude(
            canonical_name=survivor.canonical_name, rank=survivor.rank
        ).exists():
            return Response(
                {'error': (
                    'All taxa being merged must share the same canonical '
                    'name and rank as the survivor'
                )},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from bims.utils.fetch_gbif import merge_taxa_data
        merge_taxa_data(excluded_taxon=survivor, taxa_list=duplicates)

        return Response({
            'ok': True,
            'survivor_id': survivor_id,
            'merged_ids': duplicate_ids,
        })


def _iucn_data_url(taxon):
    """taxon.iucn_data is a TextField that sometimes holds a real dict and
    sometimes holds the str() of one (e.g. "{'url': 'https://...'}") - pull
    just the URL out either way."""
    data = taxon.iucn_data
    if isinstance(data, dict):
        return data.get('url', '') or ''
    if isinstance(data, str) and data.strip():
        try:
            parsed = ast.literal_eval(data)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, dict):
            return parsed.get('url', '') or ''
        return data
    return ''


class TaxaIucnLookupView(SuperuserRequiredMixin, APIView):
    """GET: look up a taxon's latest global Red List assessment on the
    IUCN API and return a comparison of local vs IUCN data, so the
    validation page can preview a fix before applying it."""

    def get(self, request, taxon_id):
        try:
            taxon = Taxonomy.objects.select_related('iucn_status').get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        if not preferences.SiteSetting.iucn_api_key:
            return Response(
                {'error': 'IUCN API key is not configured.'},
                status=status.HTTP_400_BAD_REQUEST)

        original = {
            'category': taxon.iucn_status.category if taxon.iucn_status else '',
            'label': taxon.iucn_status.get_status() if taxon.iucn_status else '',
            'sis_id': taxon.iucn_redlist_id,
            'url': _iucn_data_url(taxon),
        }

        iucn_status, sis_id, iucn_url = get_iucn_status(taxon=taxon)

        if not iucn_status and not sis_id and not iucn_url:
            return Response({
                'ok': True,
                'taxon_id': taxon_id,
                'original': original,
                'iucn': None,
            })

        proposed = {
            'category': iucn_status.category if iucn_status else '',
            'label': iucn_status.get_status() if iucn_status else '',
            'sis_id': sis_id,
            'url': iucn_url or '',
        }

        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'original': original,
            'iucn': proposed,
        })


class TaxaApplyIucnFixView(SuperuserRequiredMixin, APIView):
    """POST: apply a previously-fetched IUCN global assessment to a taxon."""

    def post(self, request):
        try:
            taxon_id = int(request.data['taxon_id'])
            iucn = request.data['iucn']
            if not isinstance(iucn, dict):
                raise TypeError
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'taxon_id and iucn payload are required'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            taxon = Taxonomy.objects.get(pk=taxon_id)
        except Taxonomy.DoesNotExist:
            return Response(
                {'error': 'Taxon not found'}, status=status.HTTP_404_NOT_FOUND)

        category = (iucn.get('category') or '').strip()
        url = (iucn.get('url') or '').strip()
        try:
            sis_id = int(iucn.get('sis_id')) if iucn.get('sis_id') else None
        except (TypeError, ValueError):
            sis_id = None

        update_fields = []

        if category:
            # Re-resolve locally rather than trusting a client-supplied FK id.
            iucn_status = get_global_iucn_status(category)
            if iucn_status and taxon.iucn_status_id != iucn_status.id:
                taxon.iucn_status = iucn_status
                update_fields.append('iucn_status')

        if sis_id and taxon.iucn_redlist_id != sis_id:
            taxon.iucn_redlist_id = sis_id
            update_fields.append('iucn_redlist_id')

        if url:
            if _iucn_data_url(taxon) != url:
                taxon.iucn_data = {'url': url}
                update_fields.append('iucn_data')

        if update_fields:
            taxon.save(update_fields=update_fields)

        return Response({
            'ok': True,
            'taxon_id': taxon_id,
            'updated_fields': update_fields,
        })


class TaxaColCheckStartView(SuperuserRequiredMixin, APIView):
    """POST: start a background check for taxa whose col_id no longer
    resolves on the Catalogue of Life checklist."""

    def post(self, request):
        taxon_group_id = request.data.get('taxonGroup') or None
        auto_remove = bool(request.data.get('auto_remove'))

        existing = DataUpstreamDeletionCheckSession.objects.filter(
            taxon_group_id=taxon_group_id,
            status__in=['pending', 'running'],
        ).order_by('-created_at').first()
        if existing:
            return Response(
                {
                    'error': 'A check is already running for this taxon group.',
                    'session_id': existing.id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        check_session = DataUpstreamDeletionCheckSession.objects.create(
            started_by=request.user if request.user.is_authenticated else None,
            taxon_group_id=taxon_group_id,
            auto_remove=auto_remove,
        )

        from bims.tasks.col_deletion_check import check_col_deletions_task
        check_col_deletions_task.delay(check_session.id)

        return Response({'ok': True, 'session_id': check_session.id})


class TaxaColCheckStatusView(SuperuserRequiredMixin, APIView):
    """GET: poll the progress of a running/completed CoL deletion check."""

    def get(self, request, session_id):
        try:
            check_session = DataUpstreamDeletionCheckSession.objects.get(pk=session_id)
        except DataUpstreamDeletionCheckSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'ok': True,
            'session_id': check_session.id,
            'status': check_session.status,
            'total': check_session.total,
            'processed': check_session.processed,
            'found_count': check_session.found_count,
            'removed_count': check_session.removed_count,
            'auto_remove': check_session.auto_remove,
            'canceled': check_session.canceled,
            'started_at': check_session.started_at,
            'finished_at': check_session.finished_at,
            'error_message': check_session.error_message,
        })


class TaxaColCheckResultsView(SuperuserRequiredMixin, APIView):
    """GET: paginated list of taxa found deleted on CoL for a session."""

    def get(self, request, session_id):
        try:
            offset = int(request.query_params.get('offset', 0))
            limit = int(request.query_params.get('limit', 50))
            limit = min(limit, 200)
        except (TypeError, ValueError):
            offset, limit = 0, 50

        qs = DataUpstreamDeletionCheckResult.objects.filter(
            session_id=session_id).order_by('name')
        total = qs.count()
        page = qs[offset: offset + limit]
        rows = [{
            'id': r.id,
            'taxon_id': r.object_id,
            'canonical_name': r.name,
            'rank': r.content_object.rank if r.content_object else '',
            'col_id': r.upstream_id,
            'detail': r.detail,
            'removed': r.removed,
            'removed_auto': r.removed_auto,
        } for r in page]

        return Response({'total': total, 'offset': offset, 'results': rows})


class TaxaColCheckRemoveView(SuperuserRequiredMixin, APIView):
    """POST: remove (null) the col_id for one CoL deletion check finding."""

    def post(self, request):
        try:
            result_id = int(request.data['result_id'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'result_id (integer) is required'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            result = DataUpstreamDeletionCheckResult.objects.select_related(
                'session').get(pk=result_id)
        except DataUpstreamDeletionCheckResult.DoesNotExist:
            return Response(
                {'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)

        if result.removed:
            return Response({'ok': True, 'already_removed': True})

        taxon = result.content_object
        if taxon is None:
            return Response(
                {'error': 'Underlying record no longer exists'},
                status=status.HTTP_404_NOT_FOUND)
        taxon.col_id = None
        taxon.save(update_fields=['col_id'])

        result.removed = True
        result.removed_auto = False
        result.removed_at = timezone.now()
        result.save(update_fields=['removed', 'removed_auto', 'removed_at'])

        DataUpstreamDeletionCheckSession.objects.filter(
            pk=result.session_id).update(removed_count=F('removed_count') + 1)

        return Response({
            'ok': True,
            'result_id': result_id,
            'taxon_id': taxon.id,
        })


class TaxaColCheckDeleteTaxonView(SuperuserRequiredMixin, APIView):
    """POST: permanently delete a taxon found deleted on CoL, along with
    its occurrence records and any child taxa (and their occurrences)."""

    def post(self, request):
        from bims.models.biological_collection_record import (
            BiologicalCollectionRecord,
        )

        try:
            result_id = int(request.data['result_id'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'result_id (integer) is required'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            result = DataUpstreamDeletionCheckResult.objects.select_related(
                'session').get(pk=result_id)
        except DataUpstreamDeletionCheckResult.DoesNotExist:
            return Response(
                {'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)

        taxon = result.content_object
        if taxon is None:
            return Response(
                {'error': 'Underlying taxon no longer exists'},
                status=status.HTTP_404_NOT_FOUND)

        taxon_ids = list(taxon.get_all_children().values_list(
            'id', flat=True)) + [taxon.id]

        occurrence_qs = BiologicalCollectionRecord.objects.filter(
            taxonomy_id__in=taxon_ids)
        deleted_occurrence_count = occurrence_qs.count()
        occurrence_qs.delete()

        deleted_taxa_count = len(taxon_ids)
        Taxonomy.objects.filter(id__in=taxon_ids).delete()

        if not result.removed:
            result.removed = True
            result.removed_auto = False
            result.removed_at = timezone.now()
            result.save(update_fields=['removed', 'removed_auto', 'removed_at'])

            DataUpstreamDeletionCheckSession.objects.filter(
                pk=result.session_id).update(removed_count=F('removed_count') + 1)

        return Response({
            'ok': True,
            'result_id': result_id,
            'taxon_id': taxon.id,
            'deleted_taxa_count': deleted_taxa_count,
            'deleted_occurrence_count': deleted_occurrence_count,
        })


class TaxaColCheckCancelView(SuperuserRequiredMixin, APIView):
    """POST: request cancellation of a running CoL deletion check."""

    def post(self, request):
        try:
            session_id = int(request.data['session_id'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'session_id (integer) is required'},
                status=status.HTTP_400_BAD_REQUEST)

        updated = DataUpstreamDeletionCheckSession.objects.filter(
            pk=session_id, status__in=['pending', 'running'],
        ).update(canceled=True)

        if not updated:
            return Response(
                {'error': 'No running session found for this id'},
                status=status.HTTP_404_NOT_FOUND)

        return Response({'ok': True, 'session_id': session_id})
