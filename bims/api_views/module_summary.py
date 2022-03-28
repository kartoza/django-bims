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
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=taxon_group
        )
        summary = dict(
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
        for key in summary.keys():
            if key in iucn_category:
                updated_summary[iucn_category[key]] = summary[key]
        summary = updated_summary
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
        if taxon_group.logo:
            summary['icon'] = taxon_group.logo.url
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
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=invert_group
        )
        invert_summary = dict()
        invert_summary[
            'total'] = collections.count()
        invert_summary[
            'total_site'] = (
            collections.distinct('site').count()
        )
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
        invert_summary['ecological_data'] = list(
            site_visit_ecological
        )
        invert_summary['total_sass'] = SiteVisit.objects.all().count()
        return invert_summary

    def algae_data(self):
        species_group = get_species_group(self.ALGAE_KEY)
        algae_summary = {}
        if not species_group:
            return {}
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=species_group
        )
        algae_summary['total'] = collections.count()
        algae_summary['total_site'] = collections.distinct('site').count()
        return algae_summary

    def odonate_data(self):
        taxon_group = get_species_group(self.ODONATE_KEY)
        if not taxon_group:
            return {}
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=taxon_group
        )
        summary = dict()
        summary['endemism'] = dict(
            collections.annotate(
                value=Case(When(taxonomy__endemism__isnull=False,
                                then=F('taxonomy__endemism__name')),
                           default=Value('Unknown'))
            ).values('value').annotate(
                count=Count('value')
            ).values_list('value', 'count')
        )
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
