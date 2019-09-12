from sass.models import SassValidationStatus
from scripts.importer.fbis_importer import FbisImporter


class FbisSassValidationStatusImporter(FbisImporter):

    content_type_model = SassValidationStatus
    table_name = 'SASSValidationStatus'

    def process_row(self, row, index):
        missing_ind = 0

        if self.get_row_value('MissingInd'):
            missing_ind = int(self.get_row_value('MissingInd'))

        (
            validation_status, created
        ) = SassValidationStatus.objects.get_or_create(
            status=self.get_row_value('Status'),
            colour=self.get_row_value('Colour'),
            colour_description=self.get_row_value('ColourDescription'),
            missing_ind=missing_ind
        )

        self.save_uuid(
            uuid=self.get_row_value('SASSValidationStatusID'),
            object_id=validation_status.id
        )
