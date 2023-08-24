from rest_framework.views import APIView
from rest_framework.response import Response
from allauth.utils import get_user_model
from django.db.models import Count, F, Case, When, Value, Q
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus,
    UploadSession,
    DownloadRequest,
    Survey
)
from bims.models.taxonomy import Taxonomy
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
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
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=taxon_group)

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
        origin_data = dict(
            collections.exclude(taxonomy__origin__exact='').values(
                'taxonomy__origin').annotate(
                count=Count('taxonomy__origin')
            ).values_list('taxonomy__origin', 'count'))
        updated_origin_data = {}
        origin_category = dict(Taxonomy.CATEGORY_CHOICES)
        for key in origin_data.keys():
            updated_origin_data[origin_category[key]] = (
                origin_data[key]
            )
        return updated_origin_data

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
            collections.exclude(taxonomy__origin__exact='').annotate(
                value=Case(When(taxonomy__iucn_status__isnull=False,
                                then=F('taxonomy__iucn_status__category')),
                           default=Value('Not evaluated'))
            ).values('value').annotate(
                count=Count('value')
            ).values_list('value', 'count')
        )
        iucn_category = dict(IUCNStatus.CATEGORY_CHOICES)
        updated_summary = {}
        for key in summary_temp.keys():
            if key in iucn_category:
                updated_summary[iucn_category[key]] = summary_temp[key]
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

        counts = (
            BiologicalCollectionRecord.objects.all().aggregate(
                total_occurrences=Count('id')),
            Taxonomy.objects.all().aggregate(total_taxa=Count('id')),
            get_user_model().objects.filter(
                last_login__isnull=False
            ).aggregate(total_users=Count('id')),
            {'total_uploads': upload_counts},
            DownloadRequest.objects.filter(
                request_category__icontains='occurrence')
            .aggregate(total_downloads=Count('id'))
        )

        return {key: value for d in counts for key, value in d.items()}

    def get(self, request, *args):
        response_data = dict()
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        ).order_by('display_order')
        response_data['general_summary'] = self.general_summary_data()
        for taxon_group in taxon_groups:
            taxon_group_name = taxon_group.name
            response_data[taxon_group_name] = (
                self.module_summary_data(taxon_group)
            )
        return Response(response_data)
