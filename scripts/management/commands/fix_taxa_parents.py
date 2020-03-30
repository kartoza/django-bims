# -*- coding: utf-8 -*-
import logging
from django.core.management.base import BaseCommand
from django.db.models import Q, signals
from bims.models import Taxonomy, TaxonGroup
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif, merge_taxa_data, check_taxa_duplicates
)
from bims.models import BiologicalCollectionRecord, taxonomy_pre_save_handler

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    taxon_rank = [
        'KINGDOM',
        'PHYLUM',
        'CLASS',
        'ORDER',
        'FAMILY',
        'GENUS',
        'SPECIES'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            '--taxon-group',
            dest='taxon_group',
            default='',
            help='Taxon Group'
        )
        parser.add_argument(
            '-i',
            '--identifier',
            dest='identifier',
            default='',
            help='Identifier for filters'
        )
        parser.add_argument(
            '-ti',
            '--taxa-identifier',
            dest='taxa_identifier',
            default='',
            help='Identifier for taxa filters'
        )

    def handle(self, *args, **options):
        taxon_group = options.get('taxon_group')
        identifier = options.get('identifier')
        taxa_identifier = options.get('taxa_identifier')
        signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
            sender=Taxonomy
        )
        filters = dict()
        taxonomies = []
        if taxon_group:
            taxon_groups = TaxonGroup.objects.filter(
                name__iexact=taxon_group,
                category='SPECIES_MODULE'
            )
            taxon_group = taxon_groups[0]
            for group in taxon_groups:
                taxonomies.extend(
                    list(group.taxonomies.values_list('id', flat=True)))

            or_condition = Q()
            group_filters = [
                'id__in',
                'parent__id__in',
                'parent__parent__id__in',
                'parent__parent__parent__id__in',
                'parent__parent__parent__parent__id__in',
            ]
            for group_filter in group_filters:
                or_condition |= Q(**{
                    group_filter: taxonomies})
            taxa = Taxonomy.objects.filter(or_condition)
        else:
            taxa = Taxonomy.objects.all()
        if taxa_identifier:
            taxa_identifiers = taxa_identifier.split('=')
            filters[taxa_identifiers[0]] = taxa_identifiers[1]
            taxa = Taxonomy.objects.filter(additional_data__contains=filters)
        elif identifier:
            identifiers = identifier.split('=')
            filters[identifiers[0]] = identifiers[1]
            bio = BiologicalCollectionRecord.objects.filter(
                additional_data__contains=filters
            )
            bio_taxa = Taxonomy.objects.filter(
                id__in=bio.values('taxonomy')
            )
            for taxon in bio_taxa:
                taxon_class = taxon.taxon_class
                if taxon_class and not taxon_group.taxonomies.filter(
                    id=taxon_class.id
                ).exists():
                    print('Add {taxon} to {group}'.format(
                        taxon=taxon_class,
                        group=taxon_group
                    ))
                    taxon_group.taxonomies.add(taxon_class)
            taxa = bio_taxa

        max_try = 10
        for taxon in taxa:
            current_taxon = taxon
            current_try = 0
            while current_taxon.rank != 'KINGDOM' and current_try < max_try:
                print(current_taxon)
                # Check for duplicates
                check_taxa_duplicates(
                    taxon_name=current_taxon.canonical_name,
                    taxon_rank=current_taxon.rank
                )
                if current_taxon:
                    try:
                        if not current_taxon.parent:
                            # Try fetch parent of taxon
                            print('fetch parent')
                            fetch_all_species_from_gbif(
                                species=current_taxon.canonical_name.strip(),
                                taxonomic_rank=current_taxon.rank,
                                gbif_key=current_taxon.gbif_key,
                                parent=None,
                                should_get_children=False
                            )
                            try:
                                current_taxon = Taxonomy.objects.get(
                                    gbif_key=current_taxon.gbif_key
                                )
                            except Taxonomy.DoesNotExist:
                                break
                            except Taxonomy.MultipleObjectsReturned:
                                _taxon = Taxonomy.objects.filter(
                                    gbif_key=current_taxon.gbif_key,
                                    parent__isnull=False
                                )
                                if not _taxon.exists():
                                    _taxon = Taxonomy.objects.filter(
                                        gbif_key=current_taxon.gbif_key
                                    )
                                merge_taxa_data(
                                    current_taxon.gbif_key,
                                    _taxon[0]
                                )
                                current_taxon = _taxon[0]
                            if current_taxon.parent:
                                current_taxon = current_taxon.parent
                            else:
                                break
                        else:
                            current_taxon = current_taxon.parent

                    except Taxonomy.DoesNotExist:
                        pass
                else:
                    break
                current_try += 1
