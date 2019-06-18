# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Count

from sass.models import (
    SiteVisitTaxon,
    SassTaxon
)


class Command(BaseCommand):
    """
    - Find all sass records which has rating scale
    - Get the duplicates ( same site visit + same sass taxon )
    - Keep sass record with biggest rating scale, remove others
    """

    def handle(self, *args, **options):
        sass_taxa = SassTaxon.objects.filter(
            rating_scale__isnull=False
        ).distinct('taxon')

        for sass_taxon in sass_taxa:
            site_visit_taxa = SiteVisitTaxon.objects.filter(
                sass_taxon__taxon=sass_taxon.taxon)

            duplicates = site_visit_taxa.values('site_visit').annotate(
                Count('site_visit')).order_by().filter(site_visit__count__gt=1)

            for duplicate in duplicates:
                dupe_site_visit_taxa = site_visit_taxa.filter(
                    site_visit=duplicate['site_visit']).order_by(
                    '-sass_taxon__rating_scale'
                )
                biggest_rating = (
                    dupe_site_visit_taxa[0].sass_taxon.rating_scale
                )
                to_be_removed = dupe_site_visit_taxa.exclude(
                    sass_taxon__rating_scale=biggest_rating)
                if to_be_removed:
                    to_be_removed.delete()
