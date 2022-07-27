from rest_framework.views import APIView
from rest_framework.response import Response
from preferences import preferences
from django.db.models import Count, F, Case, When, Value
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus
)
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
    Summary for FBIS species module
    """
    FISH_KEY = 'fish'
    INVERTEBRATE_KEY = 'invert'
    ALGAE_KEY = 'algae'
    ODONATE_KEY = 'odonate'
    ANURA = 'anura'

    def module_summary_data(self, taxon_group):
        """
        Return summary data for module
        :param taxon_group: taxon group object
        :return: dict of summary data
        """
        summary = {}
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=taxon_group
        )
        if taxon_group.chart_data == 'conservation status':
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
            summary['conservation-status'] = updated_summary

        elif taxon_group.chart_data == 'division':
            summary['division'] = collections.values(
                'taxonomy__additional_data__Division').annotate(
                count=Count('taxonomy__additional_data__Division')
            ).values('taxonomy__additional_data__Division', 'count')
        elif taxon_group.chart_data == 'origin':
            summary['origin'] = dict(collections.exclude(taxonomy__origin__exact='').values(
                'taxonomy__origin').annotate(
                count=Count('taxonomy__origin')).values_list('taxonomy__origin', 'count'))

        elif taxon_group.chart_data == 'endemism':
            summary['endemism'] = dict(collections.annotate(
                value=Case(When(taxonomy__endemism__isnull=False,
                                then=F('taxonomy__endemism__name')),
                           default=Value('Unknown'))
            ).values('value').annotate(
                count=Count('value')).values_list('value', 'count'))

        else:
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
        return summary

    def fish_data(self):
        """
        Returns fish summary
        :return: dict of fish summary
        """
        fish_group = get_species_group(self.FISH_KEY)
        if not fish_group:
            return {}
        return self.module_summary_data(fish_group)

    def anura_data(self):
        """
        Return anura summary
        :return: dict of anura sumary
        """
        anura_group = get_species_group(self.ANURA)
        if not anura_group:
            return {}
        return self.module_summary_data(anura_group)

    def invertebrate_data(self):
        """
        Returns invertebrate summary
        :return: dict of invertebrate summary
        """
        invert_group = get_species_group(self.INVERTEBRATE_KEY)
        if not invert_group:
            return {}
        return self.module_summary_data(invert_group)

    def algae_data(self):
        species_group = get_species_group(self.ALGAE_KEY)
        if not species_group:
            return {}
        return self.module_summary_data(species_group)

    def odonate_data(self):
        taxon_group = get_species_group(self.ODONATE_KEY)
        if not taxon_group:
            return {}
        return self.module_summary_data(taxon_group)

    def get(self, request, *args):
        response_data = dict()
        if preferences.SiteSetting.default_data_source == 'fbis':
            response_data[self.FISH_KEY] = self.fish_data()
            response_data[self.INVERTEBRATE_KEY] = self.invertebrate_data()
            response_data[self.ALGAE_KEY] = self.algae_data()
            response_data[self.ODONATE_KEY] = self.odonate_data()
            response_data[self.ANURA] = self.anura_data()
        else:
            taxon_groups = TaxonGroup.objects.filter(
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            )
            for taxon_group in taxon_groups:
                taxon_group_name = taxon_group.name
                response_data[taxon_group_name] = (
                    self.module_summary_data(taxon_group)
                )
        return Response(response_data)
