# -*- coding: utf-8 -*-
from django.db.models import F, Count, Sum, Case, When, Q, FloatField
from django.db.models.functions import Cast, Coalesce
from sass.models import (
    SiteVisitEcologicalCondition,
    SassEcologicalCondition,
    SiteVisitTaxon,
    SassEcologicalCategory
)
from bims.models import LocationContext
from bims.utils.logger import log


def generate_site_visit_ecological_condition(site_visits):
    """
    Generate site visit ecological condition from list of site visit
    :param site_visits: list of site visit query object
    """
    for site_visit in site_visits:
        log('Generate ecological condition for site visit : {}'.format(
            site_visit.id
        ))

        site_visit_taxa = SiteVisitTaxon.objects.filter(
            site_visit=site_visit,
        )

        summary = site_visit_taxa.annotate(
            sass_id=F('site_visit__id')).values('sass_id').annotate(
            count=Count('sass_taxon'),
            sass_score=Coalesce(Sum(Case(
                When(
                    condition=Q(site_visit__sass_version=4,
                                sass_taxon__score__isnull=False,
                                taxon_abundance__isnull=False),
                    then='sass_taxon__score'),
                When(
                    condition=Q(site_visit__sass_version=5,
                                sass_taxon__sass_5_score__isnull=False,
                                taxon_abundance__isnull=False),
                    then='sass_taxon__sass_5_score'),
                default=0),
            ), 0),
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                            FloatField()),
        ).values('sass_score', 'aspt', 'count')

        if not summary:
            continue

        aspt_score = summary[0]['aspt']
        sass_score = summary[0]['sass_score']

        site_visit_ecological, created = (
            SiteVisitEcologicalCondition.objects.get_or_create(
                site_visit=site_visit,
            )
        )

        site_visit_ecological.sass_score = sass_score
        site_visit_ecological.aspt_score = aspt_score
        location_context = LocationContext.objects.filter(
            site=site_visit.location_site
        )
        eco_region = location_context.value_from_key('eco_region_1')
        geo_class = location_context.value_from_key('geo_class')

        eco_region_splits = eco_region.split(' ')
        if len(eco_region_splits) > 0:
            if eco_region_splits[0].isdigit():
                eco_region_splits.pop(0)
                eco_region = ' '.join(eco_region_splits)

        sass_ecological_conditions = (
            SassEcologicalCondition.objects.filter(
                ecoregion_level_1__icontains=eco_region.strip(),
                geomorphological_zone__icontains=geo_class.strip(),
                sass_score_precentile__isnull=False,
                aspt_score_precentile__isnull=False
            )
        )

        if not sass_ecological_conditions.exists():
            # Check combined
            sass_ecological_conditions = (
                SassEcologicalCondition.objects.filter(
                    ecoregion_level_1__icontains=eco_region.strip(),
                    geomorphological_zone__icontains='combined',
                    sass_score_precentile__isnull=False,
                    aspt_score_precentile__isnull=False
                )
            )
        found_ecological_condition = False
        for sass_ecological_condition in sass_ecological_conditions:
            if (
                    not sass_ecological_condition.sass_score_precentile and
                    not sass_ecological_condition.aspt_score_precentile
            ):
                continue
            if (
                    sass_score >
                    sass_ecological_condition.sass_score_precentile or
                    aspt_score >
                    sass_ecological_condition.aspt_score_precentile
            ):
                site_visit_ecological.ecological_condition = (
                    sass_ecological_condition.ecological_category
                )
                site_visit_ecological.save()
                found_ecological_condition = True
                log(
                    'Found ecological condition : {}'.format(
                        sass_ecological_condition.ecological_category
                    ))
                break

        if found_ecological_condition:
            continue
        # Set to lowest category
        lowest_category = SassEcologicalCategory.objects.filter(
            Q(category__icontains='e') | Q(category__icontains='f')
        ).order_by('category')
        if not lowest_category:
            continue

        log(
            'Set to lowest ecological category : {}'.format(
                lowest_category[0].category
            ))
        site_visit_ecological.ecological_condition = lowest_category[0]
        site_visit_ecological.save()
