from django.db import connection


def add_indexes_for_taxonomy():
    with connection.cursor() as cursor:
        # Get all schemas except the system schemas
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog');")
        schemas = cursor.fetchall()
        for schema in schemas:
            schema_name = schema[0]
            # Check if the table exists in the schema
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taxonomy'
                );
            """)
            table_exists = cursor.fetchone()[0]
            if table_exists:
                cursor.execute(f"""
                   SELECT EXISTS (
                       SELECT 1
                       FROM information_schema.columns
                       WHERE table_schema = '{schema_name}'
                       AND table_name = 'bims_taxonomy'
                       AND column_name = 'hierarchical_data'
                   );
               """)
                column_exists = cursor.fetchone()[0]
                if column_exists:
                    # Create the index if it does not exist
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_indexes
                                WHERE schemaname = '{schema_name}' AND tablename = 'bims_taxonomy' AND indexname = 'idx_family_name'
                            ) THEN
                                CREATE INDEX idx_family_name ON {schema_name}.bims_taxonomy ((hierarchical_data->>'family_name'));
                            END IF;
                        END
                        $$;
                    """)
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_indexes
                                WHERE schemaname = '{schema_name}' AND tablename = 'bims_taxonomy' AND indexname = 'idx_genus_name'
                            ) THEN
                                CREATE INDEX idx_genus_name ON {schema_name}.bims_taxonomy ((hierarchical_data->>'genus_name'));
                            END IF;
                        END
                        $$;
                    """)
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_indexes
                                WHERE schemaname = '{schema_name}' AND tablename = 'bims_taxonomy' AND indexname = 'idx_species_name'
                            ) THEN
                                CREATE INDEX idx_species_name ON {schema_name}.bims_taxonomy ((hierarchical_data->>'species_name'));
                            END IF;
                        END
                        $$;
                    """)
