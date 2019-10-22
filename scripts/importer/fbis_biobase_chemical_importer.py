from datetime import datetime
from scripts.importer.fbis_postgres_importer import FbisPostgresImporter
from bims.models import (
    ChemicalRecord, LocationSite, SourceReferenceBibliography
)
from bims.models import Chem


class FbisBiobaseChemicalImporter(FbisPostgresImporter):

    table_name = '"BiobaseChemicalRecord"'
    content_type_model = ChemicalRecord

    def process_row(self, row, index):
        month = self.get_row_value(
            'Month'
        )
        if month == 13:
            month = 1
        year = self.get_row_value(
            'Year'
        )
        date_string = '{year}-{month}-{day}'.format(
            day=1,
            month=month,
            year=year
        )
        location_site = self.get_object_from_uuid(
            column='BioSiteID',
            model=LocationSite
        )
        source_reference = self.get_object_from_uuid(
            column='BioReferenceID',
            model=SourceReferenceBibliography
        )
        value = self.get_row_value('ChemValue')
        if not value:
            value = None
        else:
            value = float(value)

        chem_code = self.get_row_value('ChemCode')
        chem_unit = self.get_row_value('ChemUnit')

        chem, chem_created = Chem.objects.get_or_create(
            chem_unit=chem_unit,
            chem_code=chem_code
        )
        decimal_place = self.get_row_value('DecimalPlace')
        if decimal_place:
            decimal_place = int(decimal_place)
        else:
            decimal_place = None
        chem.decimal_place = decimal_place
        chem.chem_description = self.get_row_value('ChemDescription')
        chem.save()

        chemical_record, created = ChemicalRecord.objects.get_or_create(
            date=datetime.strptime(date_string, '%Y-%m-%d'),
            location_site=location_site,
            value=value,
            chem=chem
        )

        chemical_record.additional_data = {
            'BioBaseData': True,
            'User': self.get_row_value('User'),
            'ChemDate': self.get_row_value('ChemDate')
        }
        chemical_record.source_reference = source_reference
        chemical_record.save()

        self.save_uuid(
            uuid=self.get_row_value('BioSiteVisitChemValueID'),
            object_id=chemical_record.id
        )
