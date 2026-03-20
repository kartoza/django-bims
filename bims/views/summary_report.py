import hashlib
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from preferences import preferences
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Max
from django.db import connection

from bims.helpers.get_duplicates import get_duplicate_records
from bims.models import (
    LocationSite,
    LocationContextGroup,
    BiologicalCollectionRecord,
    TaxonGroup,
    Taxonomy
)
from bims.enums import (
    TaxonomicGroupCategory
)
from bims.cache import get_cache, set_cache, delete_cache

logger = logging.getLogger(__name__)

DANGER_TEMPLATE = '<span style="color: red">{}</span>'
WARNING_TEMPLATE = '<span style="color: orange">{}</span>'
OK_TEMPLATE = '<span style="color: green">{}</span>'

# Cache keys
SUMMARY_REPORT_CACHE_KEY = 'SUMMARY_REPORT_GENERAL_CACHE'
SUMMARY_REPORT_VERSION_KEY = 'SUMMARY_REPORT_VERSION'

# Cache timeout: 24 hours (in seconds)
SUMMARY_CACHE_TIMEOUT = 60 * 60 * 24


def get_data_version():
    """
    Generate a version hash based on the current state of the data.
    Uses record counts and latest modification timestamps for fast checking.
    """
    schema_name = connection.schema_name if hasattr(connection, 'schema_name') else 'public'

    # Get counts and latest dates - these queries are fast with proper indexes
    site_count = LocationSite.objects.count()
    record_count = BiologicalCollectionRecord.objects.count()

    # Get latest record date if available
    latest_record = BiologicalCollectionRecord.objects.aggregate(
        latest=Max('collection_date')
    )['latest']
    latest_str = str(latest_record) if latest_record else ''

    # Create a version string from key metrics
    version_string = f"{schema_name}:{site_count}:{record_count}:{latest_str}"

    # Return a short hash for comparison
    return hashlib.md5(version_string.encode()).hexdigest()[:16]


def get_cache_key(base_key):
    """Get schema-aware cache key."""
    schema_name = connection.schema_name if hasattr(connection, 'schema_name') else 'public'
    return f"{base_key}_{schema_name}"


class SummaryReportView(UserPassesTestMixin, TemplateView):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False

    template_name = 'summary_report.html'


class SummaryReportGeneralApiView(APIView):
    """
    Summary report for general data.

    Results are cached and automatically invalidated when underlying data changes.
    Use ?refresh=true to force a cache refresh.
    """

    def get(self, request, *args, **kwargs):
        # Check for force refresh
        force_refresh = request.GET.get('refresh', '').lower() == 'true'

        cache_key = get_cache_key(SUMMARY_REPORT_CACHE_KEY)
        version_key = get_cache_key(SUMMARY_REPORT_VERSION_KEY)

        # Get current data version
        current_version = get_data_version()

        if not force_refresh:
            # Check if we have valid cached data
            cached_version = get_cache(version_key)
            cached_data = get_cache(cache_key)

            if cached_data and cached_version == current_version:
                logger.debug(f"Returning cached summary report (version: {current_version})")
                # Add cache info to response
                cached_data['_cached'] = True
                cached_data['_cache_version'] = current_version
                return Response(cached_data)
            else:
                if cached_data:
                    logger.info(f"Cache invalidated - version changed from {cached_version} to {current_version}")
        else:
            logger.info("Force refresh requested for summary report")

        # Generate fresh data
        logger.info("Generating fresh summary report data...")
        data = self._generate_summary_data()

        # Cache the results
        set_cache(cache_key, data, timeout=SUMMARY_CACHE_TIMEOUT)
        set_cache(version_key, current_version, timeout=SUMMARY_CACHE_TIMEOUT)

        logger.info(f"Summary report cached (version: {current_version})")

        # Add cache info to response
        data['_cached'] = False
        data['_cache_version'] = current_version

        return Response(data)

    def _generate_summary_data(self):
        """Generate the summary report data."""
        taxon_modules = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        )
        records_per_source_collection = {}
        source_collections = (
            BiologicalCollectionRecord.objects.all().values_list(
                'source_collection', flat=True
            ).distinct('source_collection')
        )

        # - Data per module
        species_per_modules = {}
        records_per_modules = {}
        sites_per_modules = {}
        for taxon_module in taxon_modules:
            species_per_modules[taxon_module.name] = {}
            records_per_modules[taxon_module.name] = {}
            sites_per_modules[taxon_module.name] = {}
            for source_collection in source_collections:
                species_per_modules[taxon_module.name][
                    str(source_collection)] = (
                    taxon_module.taxonomies.filter(
                        biologicalcollectionrecord__source_collection=
                        source_collection
                    ).distinct('id').count()
                )
                records_per_modules[taxon_module.name][
                    str(source_collection)] = (
                    BiologicalCollectionRecord.objects.filter(
                        module_group=taxon_module,
                        source_collection=source_collection
                    ).count()
                )
                sites_per_modules[taxon_module.name][
                    str(source_collection)] = (
                    BiologicalCollectionRecord.objects.filter(
                        module_group=taxon_module,
                        source_collection=source_collection
                    ).distinct('site').count()
                )

        # -- Records per source collection
        for source_collection in source_collections:
            records_per_source_collection[str(source_collection)] = (
                BiologicalCollectionRecord.objects.filter(
                    source_collection=source_collection
                ).count()
            )

        # -- Species per source collection
        total_species_per_source_collection = {}
        for source_collection in source_collections:
            total_species_per_source_collection[str(source_collection)] = (
                BiologicalCollectionRecord.objects.filter(
                    source_collection=source_collection
                ).distinct('taxonomy').count()
            )

        # -- Sites per source collection
        total_sites_per_source_collection = {}
        for source_collection in source_collections:
            total_sites_per_source_collection[str(source_collection)] = (
                BiologicalCollectionRecord.objects.filter(
                    source_collection=source_collection
                ).distinct('site').count()
            )

        return {
            'total_sites': LocationSite.objects.all().count(),
            'total_duplicated_sites': LocationSite.objects.exclude(
                site_code=''
            ).values('site_code').annotate(
                count=Count('site_code')
            ).values('site_code', 'count').filter(
                count__gt=1
            ).count(),
            'total_records': BiologicalCollectionRecord.objects.all().count(),
            'total_duplicate_records': get_duplicate_records().count(),
            'total_modules': taxon_modules.count(),
            'total_species': (
                Taxonomy.objects.filter(taxongroup__isnull=False).count()
            ),
            'species_per_module': species_per_modules,
            'records_per_modules': records_per_modules,
            'sites_per_modules': sites_per_modules,
            'total_records_per_source_collection': (
                records_per_source_collection
            ),
            'total_species_per_source_collection': (
                total_species_per_source_collection
            ),
            'total_sites_per_source_collection': (
                total_sites_per_source_collection
            )
        }


class SummaryReportLocationContextApiView(APIView):
    """Summary report for location context data"""

    def get(self, *args):
        summary_data = dict()
        location_site_total = LocationSite.objects.all().count()

        total_sites_without_location_context = (
            LocationSite.objects.filter(locationcontext__isnull=True).count()
        )
        if total_sites_without_location_context == 0:
            total_sites_without_location_context = (
                OK_TEMPLATE.format(total_sites_without_location_context)
            )
        elif (
                total_sites_without_location_context > (location_site_total / 2)
        ):
            total_sites_without_location_context = (
                DANGER_TEMPLATE.format(
                    total_sites_without_location_context
                )
            )
        else:
            total_sites_without_location_context = (
                WARNING_TEMPLATE.format(total_sites_without_location_context)
            )
        summary_data['total_sites_without_location_context'] = (
            total_sites_without_location_context
        )

        # - Total group keys
        registered_groups = preferences.GeocontextSetting.geocontext_keys.split(',')
        location_context_groups = (
            LocationContextGroup.objects.filter(
                geocontext_group_key__in=registered_groups)
        )
        incomplete_count = LocationSite.objects.annotate(
            total_group=Count('locationcontext__group')).filter(
            total_group__lt=location_context_groups.count()
        ).count()
        if incomplete_count == 0:
            incomplete_count = OK_TEMPLATE.format(incomplete_count)
        elif incomplete_count > (location_site_total / 2):
            incomplete_count = DANGER_TEMPLATE.format(incomplete_count)
        else:
            incomplete_count = WARNING_TEMPLATE.format(incomplete_count)
        summary_data['total_sites_with_incomplete_location_context'] = (
            incomplete_count
        )

        # - Summary per location context group
        groups_summary = {}
        for location_context_group in location_context_groups:
            groups_summary_count = LocationSite.objects.filter(
                locationcontext__group_id=location_context_group.id
            ).distinct('id').count()
            if groups_summary_count == location_site_total:
                groups_summary_count = OK_TEMPLATE.format(
                    groups_summary_count
                )
            elif groups_summary_count < (location_site_total / 2):
                groups_summary_count = DANGER_TEMPLATE.format(
                    groups_summary_count
                )
            else:
                groups_summary_count = WARNING_TEMPLATE.format(
                    groups_summary_count
                )
            groups_summary[location_context_group.name] = groups_summary_count

        summary_data['total_sites_per_location_context_group'] = groups_summary
        return Response(summary_data)


def invalidate_summary_cache():
    """
    Manually invalidate the summary report cache.
    Call this function when data is modified through bulk operations
    that might not trigger the automatic version check.
    """
    cache_key = get_cache_key(SUMMARY_REPORT_CACHE_KEY)
    version_key = get_cache_key(SUMMARY_REPORT_VERSION_KEY)
    delete_cache(cache_key)
    delete_cache(version_key)
    logger.info("Summary report cache invalidated manually")
