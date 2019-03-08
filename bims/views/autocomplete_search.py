import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F
from django.apps import apps
from bims.models.vernacular_name import VernacularName
from bims.models.taxonomy import Taxonomy
from bims.models.location_site import LocationSite
from bims.models.data_source import DataSource


def autocomplete(request):
    # Search from taxon name
    q = request.GET.get('q', '')
    if len(q) < 3:
        return HttpResponse([])

    suggestions = list(
        Taxonomy.objects.filter(
            canonical_name__icontains=q,
            biologicalcollectionrecord__validated=True
        ).distinct('id').
        annotate(taxon_id=F('id'), suggested_name=F('canonical_name')).
        values('taxon_id', 'suggested_name')[:10]
    )

    if len(suggestions) < 10:
        vernacular_names = list(
            VernacularName.objects.filter(
                name__icontains=q,
                taxonomy__biologicalcollectionrecord__validated=True
            ).distinct('id').
            annotate(taxon_id=F('taxonomy__id'), suggested_name=F('name')).
            values('taxon_id', 'suggested_name')[:10]
        )

        suggestions.extend(vernacular_names)

    if len(suggestions) < 10:
        sites = list(
            LocationSite.objects.filter(
                site_code__icontains=q,
                site_code__isnull=False,
                biological_collection_record__validated=True
            ).distinct('id').
            annotate(site_id=F('id'), suggested_name=F('site_code')).
            values('site_id', 'suggested_name')[:10]
        )
        suggestions.extend(sites)

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
    if not request.is_ajax() and len(q) < 2:
        data = 'fail'
    else:
        search_qs = Taxonomy.objects.filter(
            Q(canonical_name__icontains=q) |
            Q(scientific_name__icontains=q))
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
