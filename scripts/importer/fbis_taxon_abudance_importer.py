from sass.models import TaxonAbundance
from scripts.importer.fbis_importer import FbisImporter


class FbisTaxonAbundanceImporter(FbisImporter):

    content_type_model = TaxonAbundance
    table_name = 'TaxonAbundance'

    def process_row(self, row, index):
        taxon_abundance, created = TaxonAbundance.objects.get_or_create(
            abc=self.get_row_value('ABC'),
            description=self.get_row_value('Description'),
            display_order=self.get_row_value('DisplayOrder')
        )
        self.save_uuid(
            uuid=self.get_row_value('TaxonAbundanceID'),
            object_id=taxon_abundance.id
        )
