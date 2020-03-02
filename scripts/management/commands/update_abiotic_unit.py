import os
import logging
from scripts.management.csv_command import CsvCommand
from bims.utils.logger import log
from bims.models import Chem, ChemUnit, ChemicalRecord

logger = logging.getLogger('bims')

DESCRIPTION = 'Biobase or Rivers Database_Description'
CODE = 'Code'
UNIT = 'FBIS_Unit'
NAME = 'FBIS_Name'
RETAIN_IN_LIST = 'Retain variable in FBIS abiotic list'
MIN = 'Minimum'
MAX = 'Maximum'


class Command(CsvCommand):
    """
    Read abiotic unit from csv then update the abiotic records from database
    - If abiotic records from does not exist, create one
    - If there are multiple abiotic records with same unit/name, merge it
    """

    def csv_file_name(self, options):
        # Return name of the csv file
        return 'master_list_of_abiotic_data.csv'

    @property
    def csv_root_folder(self):
        dev_folder = '/home/web/django_project'
        folder_name = 'data'
        if os.path.exists(dev_folder):
            root = dev_folder
        else:
            root = '/usr/src/bims'
        return os.path.join(
            root,
            'scripts/static/{}/'.format(
                folder_name
            )
        )

    def csv_dict_reader(self, csv_reader):
        errors = []
        success = []
        units = []

        index = 2

        for row in csv_reader:
            if row[UNIT] not in units:
                units.append(row[UNIT])
            try:
                chems = Chem.objects.filter(chem_code__iexact=row[CODE])
                if chems.exists():
                    print('exist')
                else:
                    chems = Chem.objects.filter(chem_code__iexact=row[NAME])
                    if not chems.exists():
                        chem = Chem.objects.create(
                            chem_code=row[CODE] if row[CODE] else row[NAME],
                            chem_description=row[DESCRIPTION],
                        )
                        chems = Chem.objects.filter(
                            id=chem.id
                        )
                if chems.count() > 1:
                    chem_id = chems[0].id
                    # Change unit of chemical records to use the first one
                    ChemicalRecord.objects.filter(
                        chem__in=chems
                    ).update(chem=chem_id)
                    # Delete chemical units except the first one
                    chems.exclude(id=chem_id).delete()
                    chems = Chem.objects.filter(
                        id=chem_id
                    )

                if chems:
                    chem_unit = None
                    for unit in ChemUnit:
                        if unit.value == row[UNIT]:
                            chem_unit = unit
                            break
                    chems.update(
                        minimum=row[MIN] if row[MIN] else None,
                        maximum=row[MAX] if row[MAX] else None,
                        show_in_abiotic_list=row[RETAIN_IN_LIST] == 'Yes',
                        chem_code=row[CODE] if row[CODE] else row[NAME],
                        chem_description=row[DESCRIPTION],
                        chem_unit=chem_unit.name
                    )

            except Exception as e:  # noqa
                errors.append({
                    'row': index,
                    'error': str(e)
                })
            index += 1

        if len(errors) > 0: logger.debug(errors)
        log('----')
        if len(success) > 0: logger.debug(success)

        print(units)