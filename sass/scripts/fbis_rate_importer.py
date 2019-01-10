from sass.models import Rate
from sass.scripts.fbis_importer import FbisImporter


class FbisRateImporter(FbisImporter):

    content_type_model = Rate
    table_name = 'Rate'

    def process_row(self, row, index):
        rate_value = self.get_row_value('Rate', row, True)
        if not rate_value:
            rate_value = 0
        rate, created = Rate.objects.get_or_create(
            rate=rate_value,
            description=self.get_row_value('Description', row),
            group=self.get_row_value('Group', row, True),
        )

        self.save_uuid(
            uuid=self.get_row_value('RateID', row),
            object_id=rate.id
        )
