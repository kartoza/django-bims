import simplejson as json
from django.http import HttpResponse, HttpResponseBadRequest
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import BiologicalCollectionRecord


def autocomplete(request):
    try:
        sqs = SearchQuerySet().autocomplete(
            canonical_name_auto=request.GET.get('q', '')
        )[:10]
    except TypeError:
        return HttpResponseBadRequest()
    suggestions = []

    for result in sqs:
        if BiologicalCollectionRecord.objects.filter(
            taxonomy__id=result.id,
            validated=True
        ).exists():
            suggestions.append({
                'id': result.id,
                'name': result.canonical_name
            })
    the_data = json.dumps({
        'results': suggestions[:5]
    })
    return HttpResponse(the_data, content_type='application/json')
