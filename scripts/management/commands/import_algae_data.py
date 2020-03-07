from django.contrib.auth import get_user_model
from django.db.models import Q
from scripts.management.commands.import_fish_data import Command as FishCommand
from bims.models.algae_data import AlgaeData
from bims.utils.user import create_users_from_string


ANALYST = 'Analyst'
ANALYST_INSTITUTE = 'Analyst Institute'
CURATION_PROCESS = 'Curation process'
INDICATOR_CHL_A = 'Biomass Indicator: Chl A'
INDICATOR_AFDM = 'Biomass Indicator: AFDM'
AI = 'Autotrophic Index (AI)'


class Command(FishCommand):
    file_name = ''

    def import_additional_data(self, collection_record, record):
        """
        Override this to import additional data to collection_record.
        :param collection_record: BiologicalCollectionRecord object
        :param record: csv record
        """
        # -- Algae data
        try:
            algae_data, _ = AlgaeData.objects.get_or_create(
                survey=self.survey
            )
        except AlgaeData.MultipleObjectsReturned:
            algae_data = AlgaeData.objects.filter(
                survey=self.survey
            )[0]
            print('Duplicated algae data')
        algae_data.curation_process = record[CURATION_PROCESS]
        algae_data.indicator_chl_a = record[INDICATOR_CHL_A]
        algae_data.indicator_afdm = record[INDICATOR_AFDM]
        if record[AI]:
            algae_data.ai = record[AI]
        algae_data.save()

        # -- Analyst
        analyst = create_users_from_string(record[ANALYST])
        if analyst:
            analyst = analyst[0]
            analyst.organization = record[ANALYST_INSTITUTE]
            analyst.save()
            collection_record.analyst = analyst
            collection_record.save()
