from django.core.management import BaseCommand
from sass.models import *
from bims.models import *


class Command(BaseCommand):

    def handle(self, *args, **options):
        site_visits = SiteVisit.objects.all()
        print('Makes sure all the references are the same for each visit')
        index = 1
        for site_visit in site_visits:
            print('Site visit #{}'.format(index))
            index += 1

            site_visit_taxa = SiteVisitTaxon.objects.filter(
                site_visit=site_visit
            )
            if site_visit_taxa.exists():
                site_visit_taxa_with_reference = (
                    site_visit_taxa.filter(
                        source_reference__isnull=False
                    )
                )
                if site_visit_taxa_with_reference.exists():
                    print('Found site visit taxa with references')
                    _site_visit_taxa = (
                        site_visit_taxa_with_reference[0]
                    )
                    site_visit_taxa_different_reference = (
                        site_visit_taxa.exclude(
                            source_reference__id=(
                                _site_visit_taxa.source_reference.id
                            )
                        )
                    )
                    if site_visit_taxa_different_reference.exists():
                        print('Found site visit taxa with different references')
                        site_visit_taxa_different_reference.update(
                            source_reference=_site_visit_taxa.source_reference
                        )
