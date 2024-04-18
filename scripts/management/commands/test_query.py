import time
from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Execute a complex SQL query and time the process.'

    def handle(self, *args, **options):
        # Your SQL statement
        sql = """
        SELECT "bims_locationsite"."geometry_point"::bytea, "bims_locationsite"."name", "bims_locationsite"."ecosystem_type", "bims_locationsite"."id" AS "site_id" FROM "bims_locationsite" WHERE "bims_locationsite"."id" IN (SELECT V0."site_id" FROM "bims_biologicalcollectionrecord" V0 LEFT OUTER JOIN "bims_biologicalcollectionrecord_additional_observation_sites" V2 ON (V0."id" = V2."biologicalcollectionrecord_id") WHERE ((V0."owner_id" = '1' OR V0."end_embargo_date" <= '2024-03-12' OR V0."end_embargo_date" IS NULL) AND V0."site_id" IN (SELECT U0."id" FROM "bims_locationsite" U0 WHERE (U0."ecosystem_type" IN ('River', 'Wetland', 'Open waterbody', '') AND ST_Within(
            U0."geometry_point", ST_GeomFromEWKB('\\001\\003\\000\\000 \\346\\020\\000\\000\\001\\000\\000\\000\\005\\000\\000\\000\\001\\000\\000\\000@\\0019@\\214X\\314\\216\\265w>\\300\\001\\000\\000\\000@\\0019@B5%e\\274\\241A\\300\\377\\377\\377\\377\\277wC@\\026=\\322\\034\\033JA\\300\\000\\000\\000\\000\\340XB@\\306$5\\222\\344P>\\300\\001\\000\\000\\000@\\0019@\\214X\\314\\216\\265w>\\300'::bytea))
            ))))
        """

        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()

        end_time = time.time()

        # Print out the timing result
        self.stdout.write(f'Query executed in {end_time - start_time} seconds.')
        self.stdout.write(f'Number of records returned: {len(result)}')
