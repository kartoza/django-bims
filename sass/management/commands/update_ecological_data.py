# -*- coding: utf-8 -*-
import os
import csv
import logging
from django.core.management.base import BaseCommand
from sass.models.sass_ecological_category import SassEcologicalCategory

logger = logging.getLogger('bims')


class Command(BaseCommand):

    def handle(self, *args, **options):

        ecological_category_file = 'ecological_category.csv'
        folder_name = 'docs'
        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'sass/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=ecological_category_file
            ))
        logger.info(os.path.exists(file_path))

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
