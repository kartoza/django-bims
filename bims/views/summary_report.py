from rest_framework.views import APIView
from rest_framework.response import Response
from preferences import preferences
from django.db import connection
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from bims.cache import (
    get_cache,
    set_cache,
    SUMMARY_REPORT_GENERAL_CACHE,
)
from bims.helpers.get_duplicates import (
    get_duplicate_records_summary,
    get_duplicate_site_codes,
)
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

# Cache the general summary report for 24 hours.
SUMMARY_REPORT_GENERAL_CACHE_TIMEOUT = 86400

DANGER_TEMPLATE = '<span style="color: red">{}</span>'
WARNING_TEMPLATE = '<span style="color: orange">{}</span>'
OK_TEMPLATE = '<span style="color: green">{}</span>'


class SummaryReportView(UserPassesTestMixin, TemplateView):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False

    template_name = 'summary_report.html'


class SummaryReportGeneralApiView(APIView):
    """Summary report for general data"""

    def _cache_key(self):
        try:
            schema_name = str(connection.schema_name)
        except (AttributeError, TypeError):
            try:
                schema_name = connection.tenant.name if connection.tenant else ''
            except AttributeError:
                schema_name = ''
        return f'{SUMMARY_REPORT_GENERAL_CACHE}_{schema_name}'

    def get(self, *args):
        """Return the cached general report, or queue its generation.

        The report runs many aggregate queries, so it is generated in the
        background and cached. On a cache miss we trigger the task and return a
        ``processing`` status that the frontend polls on.
        """
        cached_data = get_cache(self._cache_key())
        if cached_data:
            return Response(cached_data)

        from bims.tasks.summary_report import (
            generate_general_summary_report
        )
        generate_general_summary_report.delay(str(connection.schema_name))

        return Response({
            'status': 'processing',
            'message': (
                'Summary report is being generated. '
                'Please refresh in a moment.'
            )
        })

    def summary_data(self):
        """Build the general summary report and store it in the cache."""
        duplicate_summary = get_duplicate_records_summary()
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

        summary = {
            'total_sites': LocationSite.objects.all().count(),
            'total_duplicated_sites': get_duplicate_site_codes().count(),
            'total_records': BiologicalCollectionRecord.objects.all().count(),
            'total_duplicate_records': duplicate_summary['total_records'],
            'total_duplicate_groups': duplicate_summary['total_groups'],
            'total_removable_duplicates': (
                duplicate_summary['total_redundant_records']
            ),
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
        set_cache(
            self._cache_key(),
            summary,
            timeout=SUMMARY_REPORT_GENERAL_CACHE_TIMEOUT
        )
        return summary


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
