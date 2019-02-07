import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F
from django.apps import apps
from bims.models.vernacular_name import VernacularName
from bims.models.taxonomy import Taxonomy


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
        annotate(taxon_id=F('id'), name=F('canonical_name')).
        values('taxon_id', 'name')
    )[:10]

    if len(suggestions) < 10:
        vernacular_names = list(
            VernacularName.objects.filter(
                name__icontains=q,
                taxonomy__biologicalcollectionrecord__validated=True
            ).distinct('id').
            annotate(taxon_id=F('taxonomy__id')).
            values('taxon_id', 'name')
        )[:10]

        suggestions.extend(vernacular_names)

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
