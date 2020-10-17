from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.db.models import Count
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


class SummaryReportView(TemplateView):
    template_name = 'summary_report.html'


class SummaryReportGeneralApiView(APIView):
    """Summary report for general data"""

    def get(self, *args):
        taxon_modules = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        )

        # - Species per module
        species_per_modules = {}
        for taxon_module in taxon_modules:
            species_per_modules[taxon_module.name] = (
                taxon_module.taxonomies.all().count()
            )

        # - Records per module
        records_per_modules = {}
        for taxon_module in taxon_modules:
            records_per_modules[taxon_module.name] = (
                BiologicalCollectionRecord.objects.filter(
                    module_group=taxon_module
                ).count()
            )

        return Response({
            'total_sites': LocationSite.objects.all().count(),
            'total_duplicated_sites': LocationSite.objects.exclude(
                site_code=''
            ).values('site_code').annotate(
                count=Count('site_code')
            ).values('site_code', 'count').filter(
                count__gt=1
            ).count(),
            'total_records': BiologicalCollectionRecord.objects.all().count(),
            'total_modules': taxon_modules.count(),
            'total_species': (
                Taxonomy.objects.filter(taxongroup__isnull=False).count()
            ),
            'species_per_module': species_per_modules,
            'records_per_modules': records_per_modules
        })


class SummaryReportLocationContextApiView(APIView):
    """Summary report for location context data"""

    def get(self, *args):
        summary_data = dict()
        summary_data['total_sites_without_location_context'] = (
            LocationSite.objects.filter(locationcontext__isnull=True).count()
        )

        # - Summary per location context group
        groups_summary = {}
        location_context_groups = (
            LocationContextGroup.objects.all()
        )
        for location_context_group in location_context_groups:
            groups_summary[location_context_group.name] = (
                LocationSite.objects.filter(
                    locationcontext__group_id=location_context_group.id
                ).distinct('id').count()
            )
        summary_data['total_sites_with_group'] = groups_summary

        return Response(summary_data)
