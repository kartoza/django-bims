from django.db.models import Count, Sum

# Fields that together define a duplicate biological collection record.
# Two validated records from the same source collection are considered
# duplicates when they share the same values across all of these fields.
DUPLICATE_FIELDS = (
    'site_id',
    'survey_id',
    'collection_date',
    'biotope_id',
    'specific_biotope_id',
    'substratum_id',
    'taxonomy_id',
    'abundance_number',
    'abundance_type_id',
    'source_reference_id',
    'sampling_method_id',
)


def get_duplicate_records(source_collection=None):
    """Return groups of duplicate biological collection records.

    Each row represents a set of records that share the same values across
    ``DUPLICATE_FIELDS`` and occur more than once. Every row is annotated with
    ``duplicate``, the number of records in that group.

    :param source_collection: Restrict to a source collection. Defaults to the
        configured ``default_data_source``.
    """
    from preferences import preferences
    from bims.models import (
        BiologicalCollectionRecord,
    )

    if source_collection is None:
        source_collection = preferences.SiteSetting.default_data_source

    return (
        BiologicalCollectionRecord.objects.filter(
            source_collection=source_collection,
            validated=True
        ).exclude(
            # Ignore SASS records (SiteVisitTaxon child rows).
            sitevisittaxon__isnull=False
        ).values(
            *DUPLICATE_FIELDS
        ).annotate(
            duplicate=Count('*')
        ).exclude(duplicate=1)
    )


def get_duplicate_site_codes():
    """Return site codes shared by more than one location site.

    Each row is annotated with ``duplicate``, the number of sites using that
    site code. Empty site codes are ignored.
    """
    from bims.models import LocationSite

    return (
        LocationSite.objects.exclude(site_code='')
        .values('site_code')
        .annotate(duplicate=Count('site_code'))
        .filter(duplicate__gt=1)
    )


def get_duplicate_sites():
    """Return location sites that share a site code with another site."""
    from bims.models import LocationSite

    duplicate_codes = [row['site_code'] for row in get_duplicate_site_codes()]
    return LocationSite.objects.filter(
        site_code__in=duplicate_codes
    ).order_by('site_code', 'id')


def get_duplicate_records_summary(source_collection=None):
    """Return counts that describe the duplicate records.

    - ``total_groups``: number of distinct duplicate groups.
    - ``total_records``: number of records that belong to a duplicate group
      (includes the record that would be kept for each group).
    - ``total_redundant_records``: redundant copies that could be removed,
      i.e. ``total_records`` minus one kept record per group.
    """
    groups = get_duplicate_records(source_collection)
    total_groups = groups.count()
    total_records = groups.aggregate(total=Sum('duplicate'))['total'] or 0
    return {
        'total_groups': total_groups,
        'total_records': total_records,
        'total_redundant_records': total_records - total_groups,
    }
