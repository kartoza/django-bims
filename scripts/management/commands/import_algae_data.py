from scripts.management.commands.import_fish_data import Command as FishCommand


ANALYST = 'analyst'


class Command(FishCommand):
    file_name = ''

    def import_additional_data(self, collection_record, record):
        """
        Override this to import additional data to collection_record.
        :param collection_record: BiologicalCollectionRecord object
        :param record: csv record
        """
        pass
