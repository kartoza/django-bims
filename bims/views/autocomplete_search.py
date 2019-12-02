import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.apps import apps
from bims.models.vernacular_name import VernacularName
from bims.models.taxonomy import Taxonomy
from bims.models.location_site import LocationSite
from bims.models.data_source import DataSource
from bims.models.taxon_group import TaxonGroup
from sass.models.river import River
from bims.enums import TaxonomicRank


def autocomplete(request):
    # Search from taxon name
    q = request.GET.get('q', '')
    source_collection = request.GET.get('source_collection', [])
    taxonomy_additional_filters = {}
    vernacular_additional_filters = {}
    site_additional_filters = {}
    river_additional_filters = {}

    if source_collection:
        source_collection = json.loads(source_collection)
        taxonomy_additional_filters[
            'biologicalcollectionrecord__source_collection__in'
        ] = source_collection
        vernacular_additional_filters[
            'taxonomy__biologicalcollectionrecord__source_collection__in'
        ] = source_collection
        site_additional_filters[
            'biological_collection_record__source_collection__in'
        ] = source_collection
        river_additional_filters[
            'locationsite__biological_collection_record__source_collection__in'
        ] = source_collection

    if len(q) < 3:
        return HttpResponse([])

    # Collection name
    suggestions = list(
        Taxonomy.objects.filter(
            canonical_name__icontains=q,
            biologicalcollectionrecord__validated=True,
            **taxonomy_additional_filters
        ).distinct('id').
        annotate(
            taxon_id=F('id'),
            suggested_name=F('canonical_name'),
            source=Value('Taxonomic Rank: Taxon', CharField())
        ).
        values('taxon_id', 'suggested_name', 'source')[:10]
    )

    # Taxonomy with rank
    taxonomic_ranks = [
        TaxonomicRank.ORDER.name,
        TaxonomicRank.GENUS.name,
        TaxonomicRank.FAMILY.name,
        TaxonomicRank.SUPERFAMILY.name,
    ]
    taxonomy_suggestions = Taxonomy.objects.filter(
        canonical_name__icontains=q,
        rank__in=taxonomic_ranks,
    ).distinct('canonical_name').annotate(
        taxon_id=F('id'),
        suggested_name=F('canonical_name'),
        source=Concat(Value('Taxonomy Rank : '), 'rank')
    ).values('taxon_id', 'suggested_name', 'source')[:10]
    suggestions.extend(list(taxonomy_suggestions))

    if len(suggestions) < 10:
        vernacular_names = list(
            VernacularName.objects.filter(
                name__icontains=q,
                taxonomy__biologicalcollectionrecord__validated=True,
                **vernacular_additional_filters
            ).distinct('id').
            annotate(taxon_id=F('taxonomy__id'), suggested_name=F('name')).
            values('taxon_id', 'suggested_name')[:10]
        )
        for vernacular_name in vernacular_names:
            vernacular_name['source'] = 'common name'
        suggestions.extend(vernacular_names)

    if len(suggestions) < 10:
        sites = list(
            LocationSite.objects.filter(
                site_code__icontains=q,
                site_code__isnull=False,
                biological_collection_record__validated=True,
                **site_additional_filters
            ).distinct('id').
            annotate(site_id=F('id'), suggested_name=F('site_code')).
            values('site_id', 'suggested_name')[:10]
        )
        for site in sites:
            site['source'] = 'site code'
        suggestions.extend(sites)

    if len(suggestions) < 10:
        rivers = list(
            River.objects.filter(
                name__icontains=q,
                locationsite__biological_collection_record__isnull=False,
                locationsite__biological_collection_record__validated=True,
                **river_additional_filters
            ).distinct('id').
            annotate(river_id=F('id'), suggested_name=F('name')).
            values('river_id', 'suggested_name')[:10]
        )
        for river in rivers:
            river['source'] = 'river name'
        suggestions.extend(rivers)

    the_data = json.dumps({
        'results': suggestions
    })
    return HttpResponse(the_data, content_type='application/json')


def user_autocomplete(request):
    q = request.GET.get('term', '').capitalize()
    if not request.is_ajax() and len(q) < 2:
        data = 'fail'
    else:
        user_model_str = settings.AUTH_USER_MODEL
        user_model = apps.get_model(
            app_label=user_model_str.split('.')[0],
            model_name=user_model_str.split('.')[1]
        )
        search_qs = user_model.objects.filter(
            Q(first_name__istartswith=q) |
            Q(last_name__istartswith=q))
        results = []
        for r in search_qs:
            results.append({
                'id': r.id,
                'first_name': r.first_name,
                'last_name': r.last_name
            })
        data = json.dumps(results)
    mime_type = 'application/json'
    return HttpResponse(data, mime_type)


def data_source_autocomplete(request):
    q = request.GET.get('term', '').capitalize()
    if not request.is_ajax() and len(q) < 2:
        data = 'fail'
    else:
        search_qs = DataSource.objects.filter(
            name__icontains=q
        )
        results = []
        for r in search_qs:
            results.append({
                'id': r.id,
                'name': r.name,
            })
        data = json.dumps(results)
    mime_type = 'application/json'
    return HttpResponse(data, mime_type)


def species_autocomplete(request):
    """
    Autocomplete request for species
    :return: dict of species with id and name
    """
    q = request.GET.get('term', '').capitalize()
    exclude = request.GET.get('exclude', '')
    exclude_list = exclude.split(',')
    exclude_list = filter(None, exclude_list)
    taxon_group_request = request.GET.get('taxonGroup', '')
    taxon_group_species = []
    if taxon_group_request:
        taxon_group, created = TaxonGroup.objects.get_or_create(
            name=taxon_group_request
        )
        taxon_group_species = taxon_group.taxonomies.values_list(
            'id', flat=True
        )

    if not request.is_ajax() and len(q) < 2:
        data = 'fail'
    else:
        search_qs = Taxonomy.objects.filter(
            Q(canonical_name__icontains=q) |
            Q(scientific_name__icontains=q)
        ).filter(
            Q(id__in=taxon_group_species) |
            Q(parent__in=taxon_group_species) |
            Q(parent__parent__in=taxon_group_species) |
            Q(parent__parent__parent__in=taxon_group_species) |
            Q(parent__parent__parent__parent__in=taxon_group_species) |
            Q(parent__parent__parent__parent__parent__in=taxon_group_species)
        ).exclude(
            id__in=exclude_list
        ).distinct('canonical_name')
        results = []
        for r in search_qs:
            results.append({
                'id': r.id,
                'species': r.canonical_name,
            })
        data = json.dumps(results)
    mime_type = 'application/json'
    return HttpResponse(data, mime_type)


def site_autocomplete(request):
    q = request.GET.get('q', '').capitalize()
    if len(q) > 2:
        search_qs = LocationSite.objects.filter(
            name__icontains=q)
        results = []
        for r in search_qs:
            results.append({
                'value': r.id,
                'text': r.name,
            })
        data = json.dumps(results)
        mime_type = 'application/json'
        return HttpResponse(data, mime_type)


def abiotic_autocomplete(request):
    """Autocomplete search for abiotic data."""
    from bims.models import Chem
    q = request.GET.get('q', '').capitalize()
    data = []
    if len(q) > 1:
        search_qs = Chem.objects.filter(
            chem_description__istartswith=q).exclude(
            chem_unit__iexact=''
        )
        if not search_qs.exists():
            search_qs = Chem.objects.filter(
                chem_description__icontains=q).exclude(
                chem_unit__iexact=''
            )
        if search_qs.exists():
            search_qs = search_qs.distinct('chem_unit')
        results = []
        for r in search_qs:
            results.append({
                'id': r.id,
                'desc': r.chem_description,
                'text': r.chem_code,
                'unit': r.chem_unit
            })
        data = json.dumps(results)
    mime_type = 'application/json'
    return HttpResponse(data, mime_type)
