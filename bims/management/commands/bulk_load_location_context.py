# coding=utf-8
"""
Bulk-load bioregion values into bims_locationcontext, optionally removing
all rows for a given LocationContextGroup first.

Examples
--------
# delete all rows with group_id 1844 in the public schema
python manage.py bulk_load_location_context --delete-only --group-id=1844

# load (or delete) inside a tenant schema
python manage.py bulk_load_location_context --tenant=client1 --distance=500
"""
import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from bims.models.location_context_group import LocationContextGroup
from cloud_native_gis.models.layer import Layer

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None


class Command(BaseCommand):
    help = ("Populate bims_locationcontext with nearest bioregion values, "
            "deduplicate, add unique index, or just delete all rows for "
            "a given group.  Supports --tenant.")

    schema = "public"

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            help='Tenant schema name (django-tenants). '
                 'If omitted, works in the current connection schema.'
        )
        parser.add_argument(
            '--distance',
            type=int,
            default=100,
            help='Search radius in metres (default: 100)'
        )
        parser.add_argument(
            '--group-id',
            type=int,
            default=1844,
            help='LocationContextGroup PK to target (default: 1844)'
        )
        parser.add_argument(
            '-d', '--delete-only',
            action='store_true',
            help='DELETE all location-context rows for --group-id'
        )

    def handle(self, *args, **opts):
        tenant_schema = opts['tenant']
        radius        = opts['distance']
        group_id      = opts['group_id']
        delete_only   = opts['delete_only']
        self.schema   = tenant_schema or connection.schema_name

        if tenant_schema:
            if schema_context is None:
                self.stderr.write("--tenant needs django-tenants installed.")
                sys.exit(1)

            Tenant = get_tenant_model()
            try:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
            except Tenant.DoesNotExist:
                self.stderr.write(f"Tenant '{tenant_schema}' not found.")
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self.stdout.write(f"Running in tenant schema '{tenant_schema}'")
                self._execute(radius, group_id, delete_only)
        else:
            self.stdout.write(f"Running in schema '{self.schema}'")
            self._execute(radius, group_id, delete_only)

    def _execute(self, radius, group_id, delete_only):
        if delete_only:
            self._delete_group(group_id)
            return

        self._bulk_load(radius, group_id)

    def _delete_group(self, group_id: int):
        """Hard-delete every location-context row for the given group."""
        start = datetime.now()
        with connection.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self.schema}.bims_locationcontext "
                f"WHERE group_id = %s",
                [group_id]
            )
        secs = (datetime.now() - start).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted rows where group_id = {group_id} in {secs:.2f} s"
            )
        )

    def _exec(self, cur, sql, label):
        """Execute a single SQL statement and print rowcount if relevant."""
        self.stdout.write(f"[ … ] {label} …", ending="")
        cur.execute(sql)
        if cur.rowcount != -1:
            self.stdout.write(f" {cur.rowcount} rows")
        else:
            self.stdout.write(" done")

    def _bulk_load(self, radius: int, group_id: int):
        lcg = LocationContextGroup.objects.get(pk=group_id)
        layer = Layer.objects.get(unique_id=lcg.key)

        table_name = layer.table_name
        layer_identifier = lcg.layer_identifier
        schema_gis = f"{self.schema}_gis"

        start = datetime.now()
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("""
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = %s
                          AND indexname = 'bims_locationcontext_site_group_uidx'
                        """, [self.schema])
            if cur.fetchone():
                self.stdout.write("[ = ] unique index already exists")
            else:
                self._exec(cur, f"""
                    CREATE UNIQUE INDEX bims_locationcontext_site_group_uidx
                        ON {self.schema}.bims_locationcontext (site_id, group_id);
                """, "creating unique index")

            cur.execute("""
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = %s
                          AND table_name = %s
                          AND column_name = 'geog'
                        """, [schema_gis, table_name])
            if not cur.fetchone():
                self._exec(cur,
                           f"ALTER TABLE {schema_gis}.{table_name} ADD COLUMN geog geography;",
                           "adding geog column")
                self._exec(cur,
                           f"UPDATE {schema_gis}.{table_name} "
                           f"SET geog = ST_Transform(geometry,4326)::geography;",
                           "back-filling geog")  # rowcount printed automatically
                self._exec(cur,
                           f"CREATE INDEX layer_{table_name}_geog_gist "
                           f"ON {schema_gis}.{table_name} USING GIST (geog);",
                           "creating GiST index on geog")
            else:
                self.stdout.write("[ = ] geog column already present")

            self._exec(cur, f"""
                WITH nearest AS (
                  SELECT DISTINCT ON (s.id)
                         s.id  AS site_id,
                         {group_id} AS group_id,
                         l."{layer_identifier}" AS value
                  FROM   fbis.bims_locationsite s
                  JOIN LATERAL (
                      SELECT "{layer_identifier}", geog
                      FROM   {schema_gis}.{table_name}
                      WHERE  "{layer_identifier}" IS NOT NULL
                         AND  ST_DWithin(s.geometry_point, geog, {radius})
                      ORDER  BY s.geometry_point <-> geog
                      LIMIT 1
                  ) l ON TRUE
                )
                INSERT INTO {self.schema}.bims_locationcontext
                    (site_id, group_id, fetch_time, value)
                SELECT site_id, group_id, NOW(), value
                FROM   nearest
                WHERE  value IS NOT NULL
                ON CONFLICT (site_id, group_id)
                DO UPDATE SET
                    fetch_time = EXCLUDED.fetch_time,
                    value      = EXCLUDED.value;
            """, "inserting / updating nearest values")

        secs = (datetime.now() - start).total_seconds()
        self.stdout.write(self.style.SUCCESS(
            f"Bulk-load for {lcg.name} finished in {secs:.2f} s"
        ))
