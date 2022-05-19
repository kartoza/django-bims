from django.test import TestCase

from bims.models import physico_chemical_chart_data
from bims.tests.model_factories import (
    ChemicalRecordF, LocationSiteF, SurveyF, ChemF,
)


class TestPhysicoChemical(TestCase):
    def setUp(self) -> None:
        self.location_site = LocationSiteF.create()
        self.survey = SurveyF.create(
            site=self.location_site
        )

    def test_physico_chemical_chart_data(self):
        chem_1 = ChemF.create(
            chem_description='desc 1'
        )
        chem_2 = ChemF.create(
            chem_description='desc 2'
        )
        chem_record = ChemicalRecordF.create(
            survey=self.survey,
            chem=chem_1,
            value=15.0
        )
        ChemicalRecordF.create(
            survey=self.survey,
            chem=chem_1,
            value=99.0
        )

        chem_record_2 = ChemicalRecordF.create(
            survey=self.survey,
            chem=chem_2,
            value=10
        )
        data = physico_chemical_chart_data(self.location_site)
        self.assertIn(
            chem_record.chem.chem_code.upper(),
            data.keys()
        )
        self.assertIn(
            chem_record_2.chem.chem_code.upper(),
            data.keys()
        )
        self.assertIsNotNone(data)
