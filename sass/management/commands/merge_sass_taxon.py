# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from bims.utils.logger import log
from sass.models import (
    SassTaxon,
    SiteVisitBiotopeTaxon,
    SiteVisitTaxon
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        sass_taxon_4 = SassTaxon.objects.filter(
            taxon_sass_4__isnull=False
        )
        for sass_taxon in sass_taxon_4:
            sass_taxon_name = sass_taxon.taxon_sass_4.lower().replace(
                '1 sp', '1')
            taxon_5 = SassTaxon.objects.filter(
                taxon_sass_5__isnull=False,
                taxon_sass_5__icontains=sass_taxon_name
            )
            if taxon_5.count() > 0:
                taxon_5 = taxon_5[0]
                log('Found taxon 5 {0}'.format(
                    taxon_5.taxon_sass_5
                ))
                site_visit_taxon = SiteVisitTaxon.objects.filter(
                    sass_taxon=taxon_5
                )
                site_visit_taxon.update(
                    sass_taxon=sass_taxon
                )
                site_visit_biotope_taxon = (
                    SiteVisitBiotopeTaxon.objects.filter(
                        sass_taxon=taxon_5
                    )
                )
                site_visit_biotope_taxon.update(
                    sass_taxon=sass_taxon
                )
                sass_taxon.sass_5_score = taxon_5.sass_5_score
                sass_taxon.taxon_sass_5 = taxon_5.taxon_sass_5
                sass_taxon.save()
                taxon_5.delete()
