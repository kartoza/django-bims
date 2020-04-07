from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, F, Case, When, Value, Q
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    Taxonomy
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
    Summary for species module created in TaxonGroup
    """
    FISH_KEY = 'fish'
    INVERTEBRATE_KEY = 'invert'
    ALGAE_KEY = 'algae'

    def fish_data(self):
        """
        Returns fish summary
        :return: dict of fish summary
        """
        fish_group = get_species_group(self.FISH_KEY)
        if not fish_group:
            return {}
        collections = BiologicalCollectionRecord.objects.filter(
            module_group=fish_group
        )
        fish_summary = dict(
            collections.exclude(category__exact='').annotate(
                value=Case(When(category__isnull=False,
                                then=F('category')),
                           default=Value('Unspecified'))
            ).values('value').annotate(
                count=Count('value')
            ).values_list('value', 'count')
        )
        unspecified = collections.filter(category__exact='').count()
        if 'Unspecified' in fish_summary:
            fish_summary['Unspecified'] += unspecified
        else:
            fish_summary['Unspecified'] = unspecified
        fish_summary[
            'total'] = collections.count()
        fish_summary[
            'total_site'] = (
            collections.distinct('site').count()
        )
        return fish_summary

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

    def get(self, request, *args):
        response_data = dict()
        response_data[self.FISH_KEY] = self.fish_data()
        response_data[self.INVERTEBRATE_KEY] = self.invertebrate_data()
        response_data[self.ALGAE_KEY] = self.algae_data()
        return Response(response_data)
