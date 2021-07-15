from django.db.models import Count
from bims.models import (
    BiologicalCollectionRecord,
)


def get_duplicate_records():
    """Returns all duplicate records"""
    return (
        BiologicalCollectionRecord.objects.values(
            'site_id', 'survey__date', 'biotope_id',
            'specific_biotope_id', 'substratum_id', 'taxonomy_id',
            'abundance_number'
        ).annotate(
            duplicate=Count('*')
        ).exclude(duplicate=1)
    )
