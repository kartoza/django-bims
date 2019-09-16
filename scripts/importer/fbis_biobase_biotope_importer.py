from scripts.importer.fbis_postgres_importer import FbisPostgresImporter
from bims.models import Biotope


class FbisBiobaseBiotopeImporter(FbisPostgresImporter):

    table_name = 'public."BioBiotope"'
    content_type_model = Biotope

    def process_row(self, row, index):
        biotope_name = self.get_row_value('Biotope')
        broad = self.get_row_value('BroadBiotope')
        specific = self.get_row_value('SpecificBiotope')
        substratum = self.get_row_value('Substratum')

        biotope, created = Biotope.objects.get_or_create(
            name=biotope_name,
            broad=broad,
            specific=specific,
            substratum=substratum
        )
        biotope.additional_data = {
            'BioBaseData': True,
            'BioBroadBiotopeID': self.get_row_value('BioBroadBiotopeID'),
            'BioSpecificBiotopeID': self.get_row_value('BioSpecificBiotopeID'),
            'BioSubstratumID': self.get_row_value('BioSubstratumID')
        }
        biotope.save()

        self.save_uuid(
            uuid=self.get_row_value('BioBiotopeID'),
            object_id=biotope.id
        )
