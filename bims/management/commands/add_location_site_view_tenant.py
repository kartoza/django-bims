# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema_name',
            dest='schema_name',
            default='public',
        )

    def create_sql_query(self, view_name, query):
        sql = f'CREATE OR REPLACE VIEW {view_name} AS {query}'
        return sql

    def handle(self, *args, **options):
        schema_name = options.get('schema_name')
        base_table = f'{schema_name}.bims_locationsite'

        default_view_name = f'{schema_name}.default_location_site_cluster'
        empty_view_name = f'public.empty_location_site_view'

        default_query = (
            f'SELECT {base_table}.id AS site_id, '
            f'{base_table}.geometry_point, '
            f'{base_table}.name, '
            f'{base_table}.ecosystem_type '
            f'FROM {base_table}'
        )

        empty_query = (
            f'SELECT {base_table}.id AS site_id, '
            f'{base_table}.geometry_point, '
            f'{base_table}.name, '
            f'{base_table}.ecosystem_type '
            f'FROM {base_table} WHERE FALSE'
        )

        cursor = connection.cursor()
        cursor.execute(self.create_sql_query(default_view_name, default_query))
        cursor.execute(self.create_sql_query(empty_view_name, empty_query))

        self.stdout.write(self.style.SUCCESS(
            f"Views `{default_view_name}` and `{empty_view_name}` created successfully."
        ))
