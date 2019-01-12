from bims.models import Biotope as SassBiotope
from sass.scripts.fbis_importer import FbisImporter


class FbisSassBiotopeImporter(FbisImporter):

    content_type_model = SassBiotope
    table_name = 'SassBiotope'

    def process_row(self, row, index):

        sass_biotope, created = SassBiotope.objects.get_or_create(
            name=self.get_row_value('SassBiotope', row),
            display_order=self.get_row_value('Order', row),
            biotope_form=self.get_row_value('BiotopeForm', row),
            description=self.get_row_value('Description', row),
        )
        sass_biotope.additional_data = {
            'ComponentOfBiotopeID': self.get_row_value(
                'ComponentOfBiotopeID',
                row),
        }
        if self.get_row_value('ComponentOfBiotopeID'):
            component_biotope = self.get_object_from_uuid(
                column='ComponentOfBiotopeID',
                model=SassBiotope
            )
            if component_biotope:
                sass_biotope.biotope_component = component_biotope
        sass_biotope.save()

        self.save_uuid(
            uuid=self.get_row_value('SassBiotopeID', row),
            object_id=sass_biotope.id
        )
