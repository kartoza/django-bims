from django.core.management.base import BaseCommand
from django.db import connection

SQL = """
CREATE OR REPLACE FUNCTION public.search_location_sites(
    z integer,
    x integer,
    y integer,
    query_params json DEFAULT '{}'
)
RETURNS bytea
LANGUAGE plpgsql
SECURITY DEFINER
AS $func$
DECLARE
    v_token  text;
    v_schema text;
    v_ids    integer[];
    v_env    geometry;
    v_mvt    bytea;
BEGIN
    v_token  := query_params->>'token';
    v_schema := query_params->>'schema';

    -- Return empty tile when no real search is active
    IF v_token IS NULL OR v_token = '__empty__' OR v_schema IS NULL THEN
        RETURN ''::bytea;
    END IF;

    v_env := ST_TileEnvelope(z, x, y);

    -- Fetch site_ids from the tenant SearchToken table
    BEGIN
        EXECUTE format(
            'SELECT site_ids
               FROM %I.bims_searchtoken
              WHERE token = $1::uuid
                AND expires_at > NOW()
              LIMIT 1',
            v_schema
        ) INTO v_ids USING v_token;
    EXCEPTION WHEN OTHERS THEN
        RETURN ''::bytea;
    END;

    IF v_ids IS NULL OR cardinality(v_ids) = 0 THEN
        RETURN ''::bytea;
    END IF;

    -- Build Mapbox Vector Tile for matching sites within the tile envelope
    -- geometry_point is stored in EPSG:4326; v_env is EPSG:3857 from ST_TileEnvelope
    BEGIN
        EXECUTE format(
            $q$
            SELECT ST_AsMVT(t, 'search_location_sites', 4096, 'geom')
            FROM (
                SELECT
                    ls.id,
                    ls.site_code,
                    COALESCE(ls.name, '') AS name,
                    ST_AsMVTGeom(
                        ST_Transform(ls.geometry_point, 3857),
                        $1,
                        4096, 64, true
                    ) AS geom
                FROM %I.bims_locationsite ls
                WHERE ls.id = ANY($2)
                  AND ls.geometry_point IS NOT NULL
                  AND ST_Transform(ls.geometry_point, 3857) && $1
            ) t
            $q$,
            v_schema
        ) INTO v_mvt USING v_env, v_ids;
    EXCEPTION WHEN OTHERS THEN
        RETURN ''::bytea;
    END;

    RETURN COALESCE(v_mvt, ''::bytea);
END;
$func$;
"""


class Command(BaseCommand):
    help = (
        'Create (or replace) the search_location_sites PostgreSQL function '
        'in the public schema so Martin can serve vector tiles for search results.'
    )

    def handle(self, *args, **options):
        # Martin reads from the public schema, so the function must live there.
        # We temporarily set search_path to public to ensure that.
        with connection.cursor() as cursor:
            cursor.execute('SET search_path = public')
            cursor.execute(SQL)
        self.stdout.write(
            self.style.SUCCESS(
                'Created public.search_location_sites successfully.'
            )
        )
        self.stdout.write(
            'Restart Martin to pick up the new function source:\n'
            '  docker compose -f deployment/docker-compose.dev.yml restart martin'
        )
