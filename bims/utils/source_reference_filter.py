import json
import operator
import urllib.parse
from functools import reduce

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from bims.models.source_reference import LIST_SOURCE_REFERENCES


def parse_json_param(request, field):
    """Parse a JSON-array query param, e.g. '[23,312]' -> [23, 312]."""
    raw_value = request.GET.get(field, None)
    if not raw_value:
        return None
    try:
        return json.loads(raw_value)
    except json.decoder.JSONDecodeError:
        try:
            return json.loads(urllib.parse.unquote(raw_value))
        except json.decoder.JSONDecodeError:
            return None


def filter_by_source_reference(queryset, request):
    """Apply the `reference` and `referenceCategory` query params to a
    queryset with a `source_reference` field, matching the filtering
    used by the main search/search-module views."""
    reference = parse_json_param(request, 'reference')
    if reference:
        queryset = queryset.filter(source_reference__in=reference)

    reference_category = parse_json_param(request, 'referenceCategory')
    if reference_category:
        clauses = [
            Q(source_reference__polymorphic_ctype=
              ContentType.objects.get_for_model(
                  LIST_SOURCE_REFERENCES[category]))
            for category in reference_category
            if category in LIST_SOURCE_REFERENCES
        ]
        if clauses:
            queryset = queryset.filter(reduce(operator.or_, clauses))

    return queryset
