from bims.models import TaxonGroup
from sass.scripts.fbis_importer import FbisImporter
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class FbisTaxonGroupImporter(FbisImporter):

    content_type_model = TaxonGroup
    table_name = 'Group'

    def process_row(self, row, index):
        group_name = self.get_row_value('GroupName')
        category = TaxonomicGroupCategory.SASS_TAXON_GROUP.name

        taxon_group, created = TaxonGroup.objects.get_or_create(
            name=group_name,
            category=category
        )

        self.save_uuid(
            uuid=self.get_row_value('GroupID'),
            object_id=taxon_group.id
        )
