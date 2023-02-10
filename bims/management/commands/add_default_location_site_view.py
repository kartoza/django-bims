# -*- coding: utf-8 -*-
import ast

import django.db
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):

    def create_sql_query(self, view_name, query):
        sql = (
            'CREATE OR REPLACE VIEW "{view_name}" AS {sql_raw}'.
            format(
                view_name=view_name,
                sql_raw=query
            ))
        return sql

    def create_view(self, view_name, query):
        sql = (
            'CREATE VIEW "{view_name}" AS {sql_raw}'.
                format(
                view_name=view_name,
                sql_raw=query
            ))
        return sql

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--replace',
            dest='replace',
            default='False',
            help='Remove the old view first')

    def handle(self, *args, **options):
        view_name = 'default_location_site_cluster'

        replace_view = ast.literal_eval(
            options.get('replace', 'False')
        )

        q = (
            'SELECT DISTINCT l.id AS site_id,'
            'l.geometry_point,'
            'l.name '
            'FROM bims_locationsite l '
            'JOIN bims_survey b ON b.site_id = l.id '
            'FULL JOIN bims_watertemperature w ON w.location_site_id = l.id ;'
        )
        query = (
            'SELECT bims_locationsite.id AS site_id,'
            'bims_locationsite.geometry_point, bims_locationsite.name '
            'FROM bims_locationsite '
            'WHERE bims_locationsite.id IN'
            '(SELECT U0.site_id AS Col1 FROM '
            'bims_biologicalcollectionrecord U0 '
            'WHERE (U0.validated = True))'
        )
        empty_view_name = settings.BIMS_PREFERENCES.get(
            'empty_location_site_cluster'
        )
        empty_query = (
            'SELECT bims_locationsite.id AS site_id,'
            'bims_locationsite.geometry_point, bims_locationsite.name '
            'FROM bims_locationsite;'
        )
        cursor = connection.cursor()
        if replace_view:
            try:
                cursor.execute(
                    '''DROP MATERIALIZED VIEW {};'''.format(
                        view_name))
            except: # noqa
                pass
        cursor.execute('''%s''' % self.create_view(
            view_name=view_name,
            query=q
        ))
        cursor.execute('''%s''' % self.create_sql_query(
            view_name=empty_view_name,
            query=empty_query
        ))
