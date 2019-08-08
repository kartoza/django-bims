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
            'SELECT DISTINCT ON (bims_biologicalcollectionrecord.site_id) '
            'bims_biologicalcollectionrecord.site_id, '
            'bims_locationsite.geometry_point, bims_locationsite.name FROM '
            'bims_biologicalcollectionrecord JOIN bims_locationsite ON '
            'bims_biologicalcollectionrecord.site_id = bims_locationsite.id '
            'WHERE bims_biologicalcollectionrecord.taxonomy_id '
            'IS NOT NULL AND bims_biologicalcollectionrecord.validated = true '
            'AND bims_biologicalcollectionrecord.source_collection '
            'IN (\'fbis\');'
        )
        cursor = connection.cursor()
        cursor.execute('''%s''' % self.create_sql_query(
            view_name=view_name,
            query=query
        ))
