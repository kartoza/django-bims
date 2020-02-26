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
    return TaxonGroup.objects.filter(
        category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        name__icontains=species
    )


class ModuleSummary(APIView):
    """
    Summary for species module created in TaxonGroup
    """
    FISH_KEY = 'fish'
    INVERTEBRATE_KEY = 'invert'

    def fish_data(self):
        """
        Returns fish summary
        :return: dict of fish summary
        """
        fish_group = get_species_group(self.FISH_KEY)
        if fish_group.count() == 0:
            return {}
        fish_group = fish_group[0]
        taxa = fish_group.taxonomies.all()

        all_taxa = list(taxa.values_list('id', flat=True))
        for taxon in taxa:
            children = taxon.get_all_children()
            children = children.filter(
                biologicalcollectionrecord__isnull=False
            ).distinct()
            all_taxa.extend(list(children.values_list('id', flat=True)))
        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__in=all_taxa
        )
        fish_summary = dict(
            collections.annotate(
                value=Case(When(category__isnull=False,
                                then=F('category')),
                           default=Value('Unspecified'))
            ).values('value').annotate(
                count=Count('value')
            ).values_list('value', 'count')
        )
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
        if invert_group.count() == 0:
            return {}
        invert_group = invert_group[0]
        taxa = invert_group.taxonomies.all()
        all_taxa = list(taxa.values_list('id', flat=True))
        taxa = Taxonomy.objects.filter(
            Q(id__in=all_taxa) |
            Q(parent__in=all_taxa) |
            Q(parent__parent__in=all_taxa) |
            Q(parent__parent__parent__in=all_taxa) |
            Q(parent__parent__parent__parent__in=all_taxa) |
            Q(parent__parent__parent__parent__parent__in=all_taxa)
        )

        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__in=taxa
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

    def get(self, request, *args):
        response_data = dict()
        response_data[self.FISH_KEY] = self.fish_data()
        response_data[self.INVERTEBRATE_KEY] = self.invertebrate_data()
        return Response(response_data)
