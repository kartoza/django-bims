from django.core.management import BaseCommand
from django.db.models import signals, F, Value, Count, CharField
from django.db.models.functions import Concat
from django.db.models import Subquery, OuterRef
from django.core.management import call_command
from sass.models import *


class Command(BaseCommand):
    # Fix mismatch date from collection record with site visit

    def handle(self, *args, **options):
        site_visit_taxa = SiteVisitTaxon.objects.exclude(
            collection_date=F('site_visit__site_visit_date')
        )
        site_visit_biotope_taxa = SiteVisitBiotopeTaxon.objects.exclude(
            date=F('site_visit__site_visit_date')
        )

        print('-----UPDATE SITE VISIT TAXON COLLECTION DATE-----')
        print(site_visit_taxa.count())
        print(site_visit_biotope_taxa.count())
        site_visit_taxa.update(
            collection_date=Subquery(
                SiteVisitTaxon.objects.filter(
                    pk=OuterRef('pk')).values(
                    'site_visit__site_visit_date')[:1]))
        site_visit_biotope_taxa.update(
            date=Subquery(
                SiteVisitBiotopeTaxon.objects.filter(
                    pk=OuterRef('pk')).values(
                    'site_visit__site_visit_date')[:1]))
        print(site_visit_taxa.count())
        print(site_visit_biotope_taxa.count())

        print('-----FIX SASS TAXA GROUP-----')
        call_command('fix_sass_taxon_group_order',
                     verbosity=0,
                     interactive=False)

        print('-----CHECK DUPLICATES-----')
        site_visit_taxa = SiteVisitTaxon.objects.annotate(
            dupe_id=Concat(
                F('taxonomy_id'),
                F('site_visit_id'),
                output_field=CharField()
            )
        )
        duplicated_site_visit_taxa = site_visit_taxa.values(
            'dupe_id').annotate(
            dupe_count=Count('dupe_id')
        ).filter(dupe_count__gt=1)
        print(duplicated_site_visit_taxa.count())
        for dupe in duplicated_site_visit_taxa:
            svt = site_visit_taxa.filter(dupe_id=dupe['dupe_id'])
            if svt.filter(source_reference__isnull=False).exists():
                print('Source reference exists')
                t = svt.filter(source_reference__isnull=True)
                if t.exists():
                    print('Remove taxa without source reference')
                    print('Remove {}'.format(t.values_list('taxonomy')))
                    t.delete()
                duplicated_reference = (
                    svt.values('source_reference_id').annotate(
                        source_reference_dupe=Count('source_reference_id'))
                )
                if duplicated_reference.count() > 0:
                    if duplicated_reference[0]['source_reference_dupe'] > 1:
                        print('Remove duplicated taxon with same references')
                        taxa = svt.filter(
                            source_reference_id=(
                                duplicated_reference[0]['source_reference_id']
                            ))
                        taxon_to_keep = taxa[0].id
                        taxa.exclude(id=taxon_to_keep).delete()
            else:
                print('Source reference does not exists')
                taxon_to_keep = svt[0].id
                svt.exclude(id=taxon_to_keep).delete()

        print('-----CHECK SITE VISIT TAXON NOT IN CORRECT GROUP-----')
        site_visit_taxa = SiteVisitTaxon.objects.exclude(
            taxonomy__taxongroup__category='SASS_TAXON_GROUP'
        )
        site_visit_biotope_taxa = SiteVisitBiotopeTaxon.objects.exclude(
            taxon__taxongroup__category='SASS_TAXON_GROUP'
        )
        print(site_visit_taxa.count())
        print(site_visit_biotope_taxa.count())