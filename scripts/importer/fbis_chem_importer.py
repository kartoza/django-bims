import sqlite3
from sass.models import Chem
from sass.enums.chem_unit import ChemUnit
from scripts.importer.fbis_importer import FbisImporter


class FbisChemImporter(FbisImporter):

    content_type_model = Chem
    table_name = 'Chem'
    chem_unit = {}

    def start_processing_rows(self):
        conn = sqlite3.connect(self.sqlite_filepath)
        cur = conn.cursor()
        cur.execute('SELECT * FROM CHEMUNIT')
        chem_unit_rows = cur.fetchall()
        cur.close()
        for chem_unit_row in chem_unit_rows:
            for chem_unit in ChemUnit:
                if chem_unit.value == chem_unit_row[1]:
                    self.chem_unit[chem_unit_row[0]] = chem_unit

    def process_row(self, row, index):
        chem_unit = None
        chem_unit_value = self.get_row_value('ChemUnitID')
        if chem_unit_value:
            chem_unit = self.chem_unit[chem_unit_value].name

        minimum = 0.0
        minimum_value = self.get_row_value(
            'Minimum',
            return_none_if_empty=True)
        if minimum_value:
            minimum = float(minimum_value)

        maximum = 0.0
        maximum_value = self.get_row_value(
            'Maximum',
            return_none_if_empty=True)
        if maximum_value:
            maximum = float(maximum_value)

        chem, created = Chem.objects.get_or_create(
            chem_code=self.get_row_value('ChemCode'),
            chem_description=self.get_row_value('ChemDescription'),
            chem_unit=chem_unit,
            minimum=minimum,
            maximum=maximum
        )

        self.save_uuid(
            uuid=self.get_row_value('ChemID'),
            object_id=chem.id
        )
