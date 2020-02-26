# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    def create_sql_query(self, view_name, query):
        sql = (
            'CREATE OR REPLACE VIEW "{view_name}" AS {sql_raw}'.
            format(
                view_name=view_name,
                sql_raw=query
            ))
        return sql

    def handle(self, *args, **options):
        view_name = 'default_fbis_location_site_cluster'
        query = (
            'SELECT bims_locationsite.id AS site_id,'
            'bims_locationsite.geometry_point, bims_locationsite.name '
            'FROM bims_locationsite '
            'WHERE bims_locationsite.id IN'
            '(SELECT U0.site_id AS Col1 FROM '
            'bims_biologicalcollectionrecord U0 '
            'WHERE (U0.source_collection IN (\'fbis\')))'
        )
        cursor = connection.cursor()
        cursor.execute('''%s''' % self.create_sql_query(
            view_name=view_name,
            query=query
        ))
