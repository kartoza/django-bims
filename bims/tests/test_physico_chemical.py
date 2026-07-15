import csv
from datetime import date

from bims.models.chemical_record import ChemicalRecord
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.scripts.physico_chemical_upload import PhysicalChemicalProcess
from core.settings.utils import absolute_path
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
        data = physico_chemical_chart_data(ChemicalRecord.objects.filter(
            id__in=[chem_record.id, chem_record_2.id]
        ))
        self.assertIn(
            chem_record.chem.chem_code.upper(),
            data.keys()
        )
        self.assertIn(
            chem_record_2.chem.chem_code.upper(),
            data.keys()
        )
        self.assertIsNotNone(data)

    def test_physico_chemical_template_site_headers(self):
        template_path = absolute_path(
            'bims',
            'static',
            'data',
            'physico_chemical_template.csv'
        )

        with open(template_path) as template_file:
            headers = next(csv.reader(template_file))

        self.assertIn('User Wetland Name', headers)
        self.assertNotIn('Original Wetland Name', headers)
        self.assertIn('Ecosystem type', headers)
        self.assertLess(
            headers.index('Ecosystem type'),
            headers.index('Notes')
        )

    def test_physico_chemical_upload_accepts_excel_date_formats(self):
        processor = OccurrenceProcessor()

        self.assertEqual(
            processor.parse_date(
                {'Sampling Date': '1988-08-31 00:00:00'}
            ).date().isoformat(),
            '1988-08-31'
        )
        self.assertEqual(
            processor.parse_date(
                {'Sampling Date': '8/31/1988'}
            ).date().isoformat(),
            '1988-08-31'
        )

    def test_physico_chemical_upload_stores_custodian(self):
        chem = ChemF.create(chem_code='TEMP')
        processor = PhysicalChemicalProcess()
        processor.survey = self.survey
        processor.physico_chemical_units = [chem.chem_code]

        updated = processor.chemical_records(
            {'TEMP': '12.3'},
            self.location_site,
            date(1988, 8, 31),
            custodian='Institute A'
        )

        self.assertTrue(updated)
        chemical_record = ChemicalRecord.objects.get(chem=chem)
        self.assertEqual(chemical_record.custodian, 'Institute A')
