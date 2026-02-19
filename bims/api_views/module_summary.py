from django.contrib.sites.models import Site
from django.db import connection
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from allauth.utils import get_user_model
from django.db.models import Count, F, Case, When, Value, Q, Subquery
from sorl.thumbnail import get_thumbnail
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus,
    DownloadRequest,
    Survey
)
from bims.models.taxonomy import Taxonomy
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.cache import get_cache, LANDING_PAGE_MODULE_SUMMARY_CACHE, set_cache, delete_cache
from sass.models.site_visit_taxon import SiteVisitTaxon
from sass.models.site_visit import SiteVisit


def get_species_group(species):
    """Query taxon_group for species group then return the queryset results"""
    taxon_group = TaxonGroup.objects.filter(
        category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        name__icontains=species
    )
    if taxon_group.exists():
        return taxon_group[0]
    else:
        return None


class ModuleSummary(APIView):
    """
    Summary for species module
    """

    def module_summary_data(self, taxon_group):
        """
        Returns summary data for a module based on the given taxon group.

        Args:
            taxon_group (Taxon): Taxon group object.

        Returns:
            dict: Dictionary containing summary data.
        """
        summary = {}

        taxonomies_subquery = taxon_group.taxonomies.values_list('id', flat=True)

        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__in=Subquery(taxonomies_subquery)
        )

        # Check the chart data type and add corresponding summary data
        if taxon_group.chart_data == 'division':
            summary['division'] = self.get_division_summary(collections)
        elif taxon_group.chart_data == 'origin':
            summary['origin'] = self.get_origin_summary(collections)
        elif taxon_group.chart_data == 'endemism':
            summary['endemism'] = self.get_endemism_summary(collections)
        elif taxon_group.chart_data == 'sass':
            summary.update(self.get_sass_summary())
        else:
            summary[
                'conservation-status'] = self.get_conservation_status_summary(
                collections)

        # Add additional details
        if taxon_group.logo:
            try:
                summary['icon'] = get_thumbnail(
                    taxon_group.logo, 'x140', crop='center'
                ).url
            except (ValueError, AttributeError):
                summary['icon'] = taxon_group.logo.url

        summary['total'] = collections.count()
        summary['total_site'] = collections.distinct('site').count()
        summary['total_site_visit'] = collections.distinct('survey').count()

        return summary

    def get_division_summary(self, collections):
        """
        Returns division summary data from the provided collections
        """
        return collections.values(
            'taxonomy__additional_data__Division').annotate(
            count=Count('taxonomy__additional_data__Division')
        ).values('taxonomy__additional_data__Division', 'count')

    def get_origin_summary(self, collections):
        """
        Returns origin summary data from the provided collections
        """
        origin_data = collections.annotate(
            origin_value=Coalesce(
                Case(
                    When(taxonomy__origin__isnull=True, then=Value('Unknown')),
                    default=F('taxonomy__origin__category')
                ),
                Value('Unknown')
            )
        ).values('origin_value').annotate(
            count=Count('origin_value')
        ).values_list('origin_value', 'count')

        return dict(origin_data)

    def get_endemism_summary(self, collections):
        """
        Returns endemism summary data from the provided collections
        """
        return dict(collections.annotate(
                value=Case(When(taxonomy__endemism__isnull=False,
                                then=F('taxonomy__endemism__name')),
                           default=Value('Unknown'))
            ).values('value').annotate(
                count=Count('value')).values_list('value', 'count'))

    def get_sass_summary(self):
        """
        Returns sass summary data
        """
        site_visit_ecological = SiteVisitTaxon.objects.filter(
            **{
                'site_visit__sitevisitecologicalcondition__'
                'ecological_condition__isnull': False,
            }
        ).annotate(
            value=F('site_visit__'
                    'sitevisitecologicalcondition__'
                    'ecological_condition__category')
        ).values('value').annotate(
            count=Count('value'),
            color=F('site_visit__'
                    'sitevisitecologicalcondition__'
                    'ecological_condition__colour')
        ).values('value', 'count', 'color').order_by(
            'value'
        )
        return {
            'ecological_data' : list(site_visit_ecological),
            'total_sass': SiteVisit.objects.all().count()
        }

    def get_conservation_status_summary(self, collections):
        """
        Returns conservation status summary data from the provided collections
        """
        summary_temp = dict(
            collections.annotate(
                value=Case(When(taxonomy__iucn_status__isnull=False,
                                then=F('taxonomy__iucn_status__category')),
                           default=Value('NE'))
            ).values('value').annotate(
                count=Count('value')
            ).values_list('value', 'count')
        )
        iucn_category = dict(IUCNStatus.CATEGORY_CHOICES)
        iucn_status = IUCNStatus.objects.filter(
            national=False
        )
        updated_summary = {
            'chart_data': {},
            'colors': []
        }
        for key in summary_temp.keys():
            if key in iucn_category:
                updated_summary['chart_data'][iucn_category[key]] = summary_temp[key]
                try:
                    updated_summary['colors'].append(
                        iucn_status.filter(category=key).first().colour
                    )
                except AttributeError:
                    updated_summary['colors'].append('#000000')

        return updated_summary

    def general_summary_data(self):
        """
        This function calculates a summary of key metrics
        including total occurrences, total taxa,
        total users, total uploads, and total downloads.

        Returns:
            dict: A dictionary containing the calculated summary metrics.
        """
        upload_counts = Survey.objects.exclude(
            Q(owner__username__icontains='gbif') |
            Q(owner__username__icontains='admin') |
            Q(owner__username__icontains='map_vm')
        ).count()

        taxon_group_ids = list(TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        ).values_list('id', flat=True))

        counts = (
            BiologicalCollectionRecord.objects.filter(
                taxonomy__taxongrouptaxonomy__taxongroup__in=taxon_group_ids
            ).aggregate(
                total_occurrences=Count('id')),
            Taxonomy.objects.filter(
                taxongrouptaxonomy__taxongroup__id__in=taxon_group_ids
            ).aggregate(total_taxa=Count('id')),
            get_user_model().objects.filter(
                Q(last_login__isnull=False) | Q(email__isnull=False)
            ).exclude(email='').distinct().aggregate(total_users=Count('id')),
            {'total_uploads': upload_counts},
            DownloadRequest.objects.all().aggregate(
                total_downloads=Count('id'))
        )

        return {key: value for d in counts for key, value in d.items()}

    def _cache_key(self):
        try:
            schema_name = str(connection.schema_name)
        except (AttributeError, TypeError):
            # Fallback to tenant name if schema_name not available
            try:
                schema_name = connection.tenant.name if connection.tenant else ''
            except AttributeError:
                schema_name = ''
        return f'{LANDING_PAGE_MODULE_SUMMARY_CACHE}_{schema_name}'

    def summary_data(self):
        module_summary = dict()
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        ).order_by('display_order')
        module_summary['general_summary'] = self.general_summary_data()
        for taxon_group in taxon_groups:
            taxon_group_name = taxon_group.name
            module_summary[taxon_group_name] = (
                self.module_summary_data(
                    taxon_group
                )
            )
        set_cache(
            self._cache_key(),
            module_summary,
            timeout=86400  # Cache for 24 hours
        )
        return module_summary

    def get(self, request, *args):
        cached_data = get_cache(self._cache_key())
        if cached_data:
            return Response(cached_data)
        # Cache miss - queue background task to generate summary
        from bims.tasks.module_summary import generate_module_summary
        schema_name = str(connection.schema_name)
        generate_module_summary.delay(schema_name)

        # Return empty response with processing status
        return Response({
            'status': 'processing',
            'message': 'Module summary is being generated. Please refresh in a moment.',
            'general_summary': {}
        })
