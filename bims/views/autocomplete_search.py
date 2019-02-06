import simplejson as json
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.db.models import Q
from django.apps import apps
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.vernacular_name import VernacularName
from bims.models.taxonomy import Taxonomy


def autocomplete(request):
    suggestions = []
    # Search from taxon name
    query = request.GET.get('q', '')
    if len(query) < 3:
        return HttpResponse([])

    try:
        sqs = SearchQuerySet().filter(
            canonical_name_char__contains=query
        )[:10]
    except TypeError:
        return HttpResponseBadRequest()

    for result in sqs:
        if BiologicalCollectionRecord.objects.filter(
            taxonomy__id=result.id,
            validated=True
        ).exists():
            suggestions.append({
                'id': result.id,
                'name': result.canonical_name
            })

    # Search from vernacular name
    sqs = SearchQuerySet().filter(
        name_char__contains=query,
        lang='eng'
    ).models(VernacularName)[:10]

    unique_vernacular_names = []
    for result in sqs:
        taxonomy = Taxonomy.objects.filter(
            vernacular_names__id=result.id
        )
        if BiologicalCollectionRecord.objects.filter(
                taxonomy__in=taxonomy,
                validated=True
        ).exists():
            if result.name.lower() in unique_vernacular_names:
                continue
            unique_vernacular_names.append(result.name.lower())
            suggestions.append({
                'id': result.id,
                'name': result.name
            })

    the_data = json.dumps({
        'results': suggestions[:10]
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
            Q(first_name__startswith=q) |
            Q(last_name__startswith=q))
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
