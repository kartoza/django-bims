# -*- coding: utf-8 -*-
from django.db.models import F, CharField, Count
from django.db.models.functions import Concat
from django.core.management.base import BaseCommand
from bims.models import Taxonomy
from bims.utils.fetch_gbif import merge_taxa_data


class Command(BaseCommand):

    def handle(self, *args, **options):
        qs = Taxonomy.objects.annotate(
            dupe_id=Concat(
                F('canonical_name')
                , F('scientific_name')
                , output_field=CharField()
            )
        )

        dupes = qs.values('dupe_id').annotate(
            dupe_count=Count('dupe_id')).filter(dupe_count__gt=1)
        for dupe in dupes:
            taxa_dupes = Taxonomy.objects.annotate(
                dupe_id=Concat(
                    F('canonical_name')
                    , F('scientific_name')
                    , output_field=CharField()
                )
            ).filter(dupe_id=dupe['dupe_id'])

            taxa = taxa_dupes

            print('merging {count} -- {dupe}'.format(
                count=taxa.count(),
                dupe=dupe['dupe_id'])
            )

            # -- Check verified
            verified_taxon = taxa[0]

            if taxa.filter(verified=True).exists():
                verified_taxon = taxa.filter(verified=True)[0]
                merge_taxa_data(excluded_taxon=verified_taxon, taxa_list=taxa)
                continue

            if taxa.filter(additional_data__isnull=False).exclude(
                additional_data={}
            ).exists():
                taxa = taxa.filter(additional_data__isnull=False).exclude(
                    additional_data={}
                )

            if taxa.filter(endemism__isnull=False).exists():
                taxa = taxa.filter(endemism__isnull=False)

            if taxa.filter(origin__isnull=False).exists():
                taxa = taxa.filter(origin__isnull=False)

            if taxa.filter(gbif_key__isnull=False).exists():
                verified_taxon = taxa.filter(gbif_key__isnull=False).order_by(
                    'gbif_key'
                )[0]

            merge_taxa_data(
                excluded_taxon=verified_taxon, taxa_list=taxa_dupes)

