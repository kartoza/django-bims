import simplejson as json
from django.http import HttpResponse, HttpResponseBadRequest
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.vernacular_name import VernacularName
from bims.models.taxonomy import Taxonomy


def autocomplete(request):
    suggestions = []
    # Search from taxon name
    try:
        sqs = SearchQuerySet().filter(
            canonical_name_char__contains=request.GET.get('q', '')
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
        name_char__contains=request.GET.get('q', ''),
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
