import time
from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Execute a complex SQL query and time the process.'

    def handle(self, *args, **options):
        # Your SQL statement to get the first 300 rows
        sql = """
            SELECT *
            FROM sanpark.bims_biologicalcollectionrecord v0
            WHERE v0.source_collection IN ('sanparks', 'gbif')
              AND v0.taxonomy_id IS NOT NULL
              AND (v0.owner_id = '1' OR v0.end_embargo_date <= '2024-10-03' OR v0.end_embargo_date IS NULL)
              AND (v0.data_type = '' OR v0.data_type IN ('public', 'sensitive'))
              AND EXISTS (
                  SELECT 1
                  FROM sanpark.bims_locationcontext u1
                  JOIN sanpark.bims_locationcontextgroup u2 ON u1.group_id = u2.id
                  WHERE 
                      (u2.key = 'sanparks_mpas_q3_2023' AND u1.value = 'Addo Elephant Marine Protected Area') 
                      OR (u2.key = 'sanparks_mpas_q3_2023' AND u1.value = 'Admiralty Zone')
                      OR (u2.key = 'sanparks_sections_2024' AND u1.value = 'Langebaan Lagoon Marine Protected Area')
              )
            LIMIT 100000;
        """

        # SQL statement to get the total count of all matching rows
        count_sql = """
            SELECT COUNT(*)
            FROM sanpark.bims_biologicalcollectionrecord v0
            WHERE v0.source_collection IN ('sanparks', 'gbif')
              AND v0.taxonomy_id IS NOT NULL
              AND (v0.owner_id = '1' OR v0.end_embargo_date <= '2024-10-03' OR v0.end_embargo_date IS NULL)
              AND (v0.data_type = '' OR v0.data_type IN ('public', 'sensitive'))
              AND EXISTS (
                  SELECT 1
                  FROM sanpark.bims_locationcontext u1
                  JOIN sanpark.bims_locationcontextgroup u2 ON u1.group_id = u2.id
                  WHERE 
                      (u2.key = 'sanparks_mpas_q3_2023' AND u1.value = 'Addo Elephant Marine Protected Area') 
                      OR (u2.key = 'sanparks_mpas_q3_2023' AND u1.value = 'Admiralty Zone')
                      OR (u2.key = 'sanparks_sections_2024' AND u1.value = 'Langebaan Lagoon Marine Protected Area')
              );
        """

        start_time = time.time()

        with connection.cursor() as cursor:
            # Execute the main query to fetch the first 300 rows
            cursor.execute(sql)
            result = cursor.fetchall()

            # Execute the count query to get the total number of rows
            cursor.execute(count_sql)
            total_count = cursor.fetchone()[0]

        end_time = time.time()

        # Print out the timing result and the number of records
        self.stdout.write(f'Query executed in {end_time - start_time:.4f} seconds.')
        self.stdout.write(f'Number of records returned: {len(result)}')
        self.stdout.write(f'Total number of matching records: {total_count}')
