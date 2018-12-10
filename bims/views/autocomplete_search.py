import simplejson as json
from django.http import HttpResponse, HttpResponseBadRequest
from haystack.query import SearchQuerySet


def autocomplete(request):
    try:
        sqs = SearchQuerySet().autocomplete(
           canonical_name_auto=request.GET.get('q', '')
        )[:5]
    except TypeError:
        return HttpResponseBadRequest()
    suggestions = [
        {
           'id': result.id,
           'name': result.canonical_name
        } for result in sqs
    ]
    the_data = json.dumps({
        'results': suggestions
    })
    return HttpResponse(the_data, content_type='application/json')
