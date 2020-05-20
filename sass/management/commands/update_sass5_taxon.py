# -*- coding: utf-8 -*-
import os
import pandas as pd
import math
from django.conf import settings
from django.core.management.base import BaseCommand
from bims.utils.gbif import search_taxon_identifier
from sass.models.sass_taxon import SassTaxon


class Command(BaseCommand):
    help = 'Update SASS5 Taxon Data'
    not_taxon_string = [
        'SASS Score',
        'No. of Taxa',
        'ASPT',
        'Other biota:',
        'Comments/Observations:',
    ]
    taxon_5_data = {
        'Belostomatidae (Giant Water Bugs)': 3,
        'Corixidae (Water boatmen)': 3,
    }

    def handle(self, *args, **options):
        display_order = 1
        excel_file_name = 'SASS5_Data_sheet.xls'
        sheet_title = 'ModifiedFieldSheet'
        sass_sheet_file = os.path.join(
            settings.MEDIA_ROOT,
            excel_file_name
        )

        if not os.path.isfile(sass_sheet_file):
            print('%s not found in media directory' % sass_sheet_file)
            return False

        xl = pd.ExcelFile(sass_sheet_file)
        df1 = xl.parse(sheet_title)

        taxon_data = False
        taxon_dict = {}

        for index, row in df1.iterrows():
            if taxon_data:
                if row.isnull().all():
                    taxon_data = False
                    continue
                row_index = 0
                for column_data in row:
                    if isinstance(column_data, basestring):
                        if (
                            not column_data.isspace() and
                            column_data not in self.not_taxon_string
                        ):
                            if row_index not in taxon_dict:
                                taxon_dict[row_index] = []
                            taxon_dict[row_index].append(
                                {
                                    column_data: row[row_index + 1]
                                }
                            )
                    row_index += 1
            if row[0] == 'Taxon':
                taxon_data = True

        for taxon_list in taxon_dict:
            for taxon_data in taxon_dict[taxon_list]:
                for taxon_complete_name, taxon_score in taxon_data.items():
                    taxon_name = taxon_complete_name.split('*')[0]
                    taxon_name = taxon_name.split(' ')[0]
                    taxonomy = search_taxon_identifier(taxon_name)
                    sass_taxon, created = SassTaxon.objects.get_or_create(
                        taxon=taxonomy,
                        taxon_sass_5=taxon_complete_name,
                        display_order_sass_5=display_order
                    )
                    if not math.isnan(taxon_score):
                        sass_taxon.sass_5_score = int(taxon_score)
                        sass_taxon.save()
                    display_order += 1
                    print('Added new taxon : %s' % taxonomy.scientific_name)
