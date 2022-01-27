from django.db.models import Count, QuerySet
from bims.models import (
    BiologicalCollectionRecord,
)


def get_duplicate_records() -> QuerySet:
    """Returns all duplicate records"""
    return (
        BiologicalCollectionRecord.objects.filter(
            sitevisittaxon__isnull=True
        ).values(
            'site_id', 'survey__date', 'collection_date', 'biotope_id',
            'specific_biotope_id', 'substratum_id', 'taxonomy_id',
            'abundance_number'
        ).annotate(
            duplicate=Count('*')
        ).exclude(duplicate=1)
    )
