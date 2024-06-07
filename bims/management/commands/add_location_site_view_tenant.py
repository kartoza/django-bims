# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema_name',
            dest='schema_name',
            default='public',)

    def create_sql_query(self, view_name, query, schema_name):
        sql = (
            'CREATE OR REPLACE VIEW {schema_name}.{view_name} AS {sql_raw}'.
            format(
                schema_name=schema_name,
                view_name=view_name,
                sql_raw=query
            ))
        return sql

    def handle(self, *args, **options):
        schema_name = options.get('schema_name')
        view_name = f'default_{schema_name}_location_site_cluster'
        query = (
            f'SELECT {schema_name}.bims_locationsite.id AS site_id,'
            f'{schema_name}.bims_locationsite.geometry_point, {schema_name}.bims_locationsite.name, {schema_name}.bims_locationsite.ecosystem_type '
            f'FROM {schema_name}.bims_locationsite;'
        )
        cursor = connection.cursor()
        cursor.execute('''%s''' % self.create_sql_query(
            view_name=view_name,
            query=query,
            schema_name=schema_name
        ))
