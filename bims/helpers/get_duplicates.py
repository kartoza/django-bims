from django.db.models import Count


def get_duplicate_records():
    """Returns all duplicate records"""
    from preferences import preferences
    from bims.models import (
        BiologicalCollectionRecord,
    )

    return (
        BiologicalCollectionRecord.objects.filter(
            source_collection=preferences.SiteSetting.default_data_source,
            validated=True
        ).values(
            'site_id',
            'survey_id',
            'biotope_id',
            'specific_biotope_id',
            'substratum_id',
            'taxonomy_id',
            'abundance_number',
            'source_reference_id',
            'sampling_method_id'
        ).annotate(
            duplicate=Count('*')
        ).exclude(duplicate=1)
    )
