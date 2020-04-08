from django.db.models import Q
from bims.models import TaxonGroup, Taxonomy
from sass.models import SassTaxon
from scripts.importer.fbis_importer import FbisImporter
from bims.utils.gbif import search_taxon_identifier


class FbisTaxonImporter(FbisImporter):

    content_type_model = SassTaxon
    table_name = 'Taxon'

    def finish_processing_rows(self):
        print('New Data total : {}'.format(len(self.new_data)))
        print('New Data : {}'.format(self.new_data))
        print('Failed Total : {}'.format(len(self.failed_messages)))
        print('Failed Messages : {}'.format(self.failed_messages))

    def process_row(self, row, index):
        taxon = self.get_object_from_uuid(
            column='TaxonID',
            model=SassTaxon
        )

        if self.only_missing and taxon:
            print('{} already exist'.format(taxon))
            return

        taxon_name = self.get_row_value('TaxonName')
        taxon_name = taxon_name.split(' ')[0]
        taxon_name = taxon_name.split('(')[0]
        taxon_name = taxon_name.split('/')[0]
        group = self.get_object_from_uuid(
            'GroupID',
            TaxonGroup
        )

        # Check existing taxonomy
        taxa = Taxonomy.objects.filter(
            Q(canonical_name__icontains=taxon_name) |
            Q(legacy_canonical_name__icontains=taxon_name)
        )

        if taxa.exists():
            taxonomy = taxa[0]
        else:
            taxonomy = search_taxon_identifier(taxon_name)

        if not taxonomy:
            # Create one
            taxonomy = Taxonomy.objects.create(
                scientific_name=taxon_name,
                legacy_canonical_name=taxon_name,
                canonical_name=taxon_name,
                rank='FAMILY'
            )

        air_breather_value = self.get_row_value(
            'AirBreather',
            return_none_if_empty=True)

        if not air_breather_value:
            air_breather_value = 0

        taxon_sass, created = SassTaxon.objects.get_or_create(
            taxon=taxonomy,
            taxon_sass_4=self.get_row_value('TaxonSASS4'),
            score=self.get_row_value(
                'Score',
                return_none_if_empty=True
            ),
            sass_5_score=self.get_row_value(
                'SASS5Score',
                return_none_if_empty=True
            ),
            air_breather=air_breather_value,
            display_order_sass_4=self.get_row_value(
                'DisplayOrderSASS4',
                return_none_if_empty=True),
            display_order_sass_5=self.get_row_value(
                'DisplayOrderSASS5',
                return_none_if_empty=True
            )
        )

        if created:
            self.new_data.append(taxon_sass.id)

        biobase_id = self.get_row_value('BioBaseID')
        if biobase_id:
            biobase_id = str(biobase_id)
        lifestage = self.get_row_value('Lifestage')
        if lifestage:
            lifestage = str(lifestage)

        taxon_sass.additional_data = {
            'TaxonK': self.get_row_value('TaxonK'),
            'TaxonOrder': self.get_row_value('TaxonOrder'),
            'Lifestage': lifestage,
            'BioBaseID': biobase_id,
        }
        taxon_sass.save()

        if group:
            group.taxonomies.add(taxonomy)
            group.save()

        self.save_uuid(
            uuid=self.get_row_value('TaxonID'),
            object_id=taxon_sass.id
        )
