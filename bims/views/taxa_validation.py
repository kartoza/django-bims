# coding=utf-8
from braces.views import SuperuserRequiredMixin
from django.db.models import F, IntegerField, Q
from django.views.generic import TemplateView

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.models.taxon_group import TaxonGroup
from bims.models.taxonomy import Taxonomy
from bims.utils.gbif import find_species

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
]


def _base_qs(taxon_group_id=None):
    qs = Taxonomy.objects.all()
    if taxon_group_id:
        qs = qs.filter(taxongroup__id=taxon_group_id)
    return qs


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


_CHECK_FN = {
    'missing_parent': _qs_missing_parent,
    'synonym_no_accepted': _qs_synonym_no_accepted,
    'accepted_is_synonym': _qs_accepted_is_synonym,
    'subspecies_synonym_parent': _qs_subspecies_synonym_parent,
    'invalid_parent_rank': _qs_invalid_parent_rank,
    'duplicate_canonical': _qs_duplicate_canonical,
    'missing_external_id': _qs_missing_external_id,
}


def run_checks(taxon_group_id=None):
    base = _base_qs(taxon_group_id)
    return {
        check['key']: _CHECK_FN[check['key']](base).count()
        for check in CHECKS
    }


def taxa_for_check(check_key, taxon_group_id=None, offset=0, limit=50):
    base = _base_qs(taxon_group_id)
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
