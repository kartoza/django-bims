from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, F, Case, When, Value
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus
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
        Return summary data for module
        :param taxon_group: taxon group object
        :return: dict of summary data
        """
        summary = {}
        collections = BiologicalCollectionRecord.objects.filter(module_group=taxon_group)

        taxonomies = collections.distinct('taxonomy').values('taxonomy__id')

        taxa = Taxonomy.objects.filter(id__in=[taxonomies])

        if taxon_group.chart_data == 'division':
            summary['division'] = taxa.values(
                'additional_data__Division').annotate(
                count=Count('additional_data__Division')
            ).values('additional_data__Division', 'count')
        elif taxon_group.chart_data == 'origin':
            origin_data = dict(
                taxa.exclude(origin__exact='').values(
                    'origin').annotate(
                    count=Count('origin')
                ).values_list('origin', 'count'))
            updated_origin_data = {}
            origin_category = dict(Taxonomy.CATEGORY_CHOICES)
            for key in origin_data.keys():
                updated_origin_data[origin_category[key]] = (
                    origin_data[key]
                )
            summary['origin'] = updated_origin_data
        elif taxon_group.chart_data == 'endemism':
            summary['endemism'] = dict(taxa.annotate(
                value=Case(When(endemism__isnull=False,
                                then=F('endemism__name')),
                           default=Value('Unknown'))
            ).values('value').annotate(
                count=Count('value')).values_list('value', 'count'))
        elif taxon_group.chart_data == 'sass':
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
            summary['ecological_data'] = list(
                site_visit_ecological
            )
            summary['total_sass'] = SiteVisit.objects.all().count()
        else:
            summary_temp = dict(
                taxa.exclude(origin__exact='').annotate(
                    value=Case(When(iucn_status__isnull=False,
                                    then=F('iucn_status__category')),
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
            summary['conservation-status'] = updated_summary
        x = TaxonGroup.objects.all().values()
        if taxon_group.logo:
            summary['icon'] = taxon_group.logo.url
        summary[
            'total'] = collections.count()
        summary[
            'total_site'] = (
            collections.distinct('site').count()
        )
        summary[
            'total_site_visit'] = (
            collections.distinct('survey').count()
        )
        summary['module_id'] = taxon_group.id

        summary['total_taxa'] = collections.distinct('taxonomy').count()
        # summary['testing'] = x

        return summary

    def get(self, request, *args):
        response_data = dict()
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        ).order_by('display_order')
        for taxon_group in taxon_groups:
            taxon_group_name = taxon_group.name
            response_data[taxon_group_name] = (
                self.module_summary_data(taxon_group)
            )
        return Response(response_data)
