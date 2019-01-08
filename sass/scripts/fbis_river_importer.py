from bims.models import (
    FbisUUID,
)
from sass.models import River
from sass.scripts.fbis_importer import FbisImporter


class FbisRiverImporter(FbisImporter):

    content_type_model = River
    table_name = 'River'

    def process_row(self, index):
        print('Processing %s of %s' % (
            index + 1,
            len(self.accdb_rows)))
        validated_value = str(self.get_row_value(index, 'Validated')) == '1.0'

        # Get owner
        owner = None
        owners = FbisUUID.objects.filter(
            uuid=self.get_row_value(index, 'OwnerID')
        )
        if owners.exists():
            owner = owners[0].content_object

        river, created = River.objects.get_or_create(
            name=self.get_row_value(index, 'RiverName'),
            owner=owner
        )
        river.validated = validated_value
        river.save()

        self.save_uuid(
            uuid=self.get_row_value(index, 'RiverID'),
            object_id=river.id
        )
