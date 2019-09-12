from bims.models import (
    FbisUUID,
)
from sass.models import River
from scripts.importer.fbis_importer import FbisImporter


class FbisRiverImporter(FbisImporter):

    content_type_model = River
    table_name = 'River'

    def process_row(self, row, index):
        validated_value = str(self.get_row_value('Validated', row)) == '1'

        # Get owner
        owner = None
        owners = FbisUUID.objects.filter(
            uuid=self.get_row_value('OwnerID', row)
        )
        if owners.exists():
            owner = owners[0].content_object

        river, created = River.objects.get_or_create(
            name=self.get_row_value('RiverName', row),
            owner=owner
        )
        river.validated = validated_value
        river.save()

        self.save_uuid(
            uuid=self.get_row_value('RiverID', row),
            object_id=river.id
        )
