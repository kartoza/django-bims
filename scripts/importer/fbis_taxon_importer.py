from bims.models import TaxonGroup
from sass.models import SassTaxon
from scripts.importer.fbis_importer import FbisImporter
from bims.utils.gbif import search_taxon_identifier


class FbisTaxonImporter(FbisImporter):

    content_type_model = SassTaxon
    table_name = 'Taxon'

    def process_row(self, row, index):
        taxon_name = self.get_row_value('TaxonName')
        taxon_name = taxon_name.split(' ')[0]
        taxon_name = taxon_name.split('(')[0]
        taxon_name = taxon_name.split('/')[0]
        group = self.get_object_from_uuid(
            'GroupID',
            TaxonGroup
        )

        taxonomy = search_taxon_identifier(taxon_name)

        if not taxonomy:
            return

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
