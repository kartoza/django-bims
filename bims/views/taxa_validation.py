# coding=utf-8
import json
from django.contrib.auth.decorators import login_required
from django.db.models import F, IntegerField, Q
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.taxon_group import TaxonGroup
from bims.models.taxonomy import Taxonomy

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
            'Taxa with no GBIF key, no FADA ID, no Aphia ID, and no '
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
    # have no GBIF/FADA/Aphia/TaxonWorks ID, so exclude them.
    bims_harvested_ids = (
        TaxonGroup.objects
        .filter(is_readonly=True, upstream_url__gt='')
        .values_list('taxonomies__id', flat=True)
    )
    return qs.filter(
        gbif_key__isnull=True,
        aphia_id__isnull=True,
        taxonworks_id__isnull=True,
    ).filter(
        Q(fada_id__isnull=True) | Q(fada_id='')
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


@method_decorator(login_required, name='dispatch')
class TaxaValidationView(TemplateView):
    template_name = 'taxa_validation.html'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Staff access required.')
        return super().dispatch(request, *args, **kwargs)

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


@login_required
def taxa_validation_results(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    check_key = request.GET.get('check', '')
    taxon_group_id = request.GET.get('taxonGroup') or None
    try:
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 50))
        limit = min(limit, 200)
    except (TypeError, ValueError):
        offset, limit = 0, 50

    if check_key not in _CHECK_FN:
        return JsonResponse({'error': 'Unknown check key'}, status=400)

    rows, total = taxa_for_check(check_key, taxon_group_id, offset, limit)
    return JsonResponse({'total': total, 'offset': offset, 'results': rows})


@login_required
def taxa_assign_gbif_key(request):
    """POST: assign a GBIF key to a taxon from the validation page."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
        taxon_id = int(body['taxon_id'])
        gbif_key = int(body['gbif_key'])
    except (KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'taxon_id and gbif_key (integers) are required'}, status=400)

    try:
        taxon = Taxonomy.objects.get(pk=taxon_id)
    except Taxonomy.DoesNotExist:
        return JsonResponse({'error': 'Taxon not found'}, status=404)

    if Taxonomy.objects.filter(gbif_key=gbif_key).exclude(pk=taxon_id).exists():
        return JsonResponse(
            {'error': f'GBIF key {gbif_key} is already used by another taxon'},
            status=409,
        )

    taxon.gbif_key = gbif_key
    taxon.save(update_fields=['gbif_key'])
    return JsonResponse({'ok': True, 'taxon_id': taxon_id, 'gbif_key': gbif_key})
