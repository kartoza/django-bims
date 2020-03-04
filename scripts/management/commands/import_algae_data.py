from django.contrib.auth import get_user_model
from django.db.models import Q
from scripts.management.commands.import_fish_data import Command as FishCommand
from bims.models.algae_data import AlgaeData
from bims.utils.user import create_users_from_string


ANALYST = 'Analyst'
ANALYST_INSTITUTE = 'Analyst Institute'
CURATION_PROCESS = 'Curation process'
INDICATOR_CHL_A = 'Biomass Indicator: Chl A'
CHL_A = 'Chlorophyll a: benthic'
INDICATOR_AFDM = 'Biomass Indicator: AFDM'
AFDM = 'AFDM'
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
        algae_data, _ = AlgaeData.objects.get_or_create(
            biological_collection_record=collection_record
        )
        algae_data.curation_process = record[CURATION_PROCESS]
        algae_data.indicator_chl_a = record[INDICATOR_CHL_A]
        if record[CHL_A]:
            algae_data.chl_a = record[CHL_A]
        algae_data.indicator_asdm = record[INDICATOR_AFDM]
        if record[AFDM]:
            algae_data.asdm = record[AFDM]
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
