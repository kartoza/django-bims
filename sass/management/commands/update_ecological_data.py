# -*- coding: utf-8 -*-
import os
import csv
import logging
from django.core.management.base import BaseCommand
from sass.models.sass_ecological_category import SassEcologicalCategory
from sass.models.sass_ecological_condition import SassEcologicalCondition

logger = logging.getLogger('bims')


class Command(BaseCommand):

    def process_csv_to_dict(self, csv_name):
        folder_name = 'docs'
        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'sass/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=csv_name
            ))

        data_length = 0
        with open(file_path) as csv_file:
            reader = csv.reader(csv_file)
            rows = [row for row in reader if row]
            headings = rows[0]

            ecological_info = {}
            for row in rows[1:]:
                data_length += 1
                for col_header, data_column in zip(headings, row):
                    ecological_info.setdefault(col_header, []).append(
                        data_column)
        return ecological_info, data_length

    def update_ecological_category(self):
        logger.info('Updating ecological category')
        ecological_category_file = 'ecological_category.csv'
        ecological_info, data_length = self.process_csv_to_dict(
            ecological_category_file)
        for i in range(data_length):
            category = ecological_info['Ecological Category'][i]
            name = ecological_info['Ecological Category Name'][i]
            description = ecological_info['Description'][i]
            colour = ecological_info['Colour'][i]

            sass_ecological_category, created = (
                SassEcologicalCategory.objects.get_or_create(
                    category=category
                )
            )
            sass_ecological_category.name = name
            sass_ecological_category.description = description
            sass_ecological_category.colour = colour
            sass_ecological_category.order = i
            sass_ecological_category.save()

    def update_ecological_conditions(self):
        logger.info('Updating ecological condition')
        ecological_condition_file = 'ecological_condition.csv'
        ecological_info, data_length = self.process_csv_to_dict(
            ecological_condition_file)

        categories = ['A', 'B', 'C', 'D']

        for i in range(data_length):
            for category in categories:
                self.update_ecological_condition(
                    ecological_info,
                    category,
                    i
                )

    def update_ecological_condition(self, ecological_info, category, index):
        ecological_category = SassEcologicalCategory.objects.get(
            category=category
        )
        sass_precentile = (
            ecological_info['SASS Score Percentiles - %s' % category][index]
        )
        aspt_precentile = (
            ecological_info['ASPT Percentiles - %s' % category][index]
        )
        ecoregion_level_1 = ecological_info['Ecoregion Level 1'][index]
        geomorphological_zone = (
            ecological_info['Geomorphological Zone'][index]
        )
        condition, created = (
            SassEcologicalCondition.objects.get_or_create(
                ecoregion_level_1=ecoregion_level_1,
                geomorphological_zone=geomorphological_zone,
                ecological_category=ecological_category
            ))
        if sass_precentile:
            condition.sass_score_precentile = int(sass_precentile)
        if aspt_precentile:
            condition.aspt_score_precentile = float(aspt_precentile)
        condition.save()

    def handle(self, *args, **options):
        self.update_ecological_category()
        self.update_ecological_conditions()
