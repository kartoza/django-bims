# Generated migration to rename taxontag_id to tag_id in bims_taggroup_tags

from django.db import migrations, connection


def rename_column_in_all_schemas(apps, schema_editor):
    """
    Rename taxontag_id column to tag_id in bims_taggroup_tags table
    across all schemas (public and tenant schemas).
    """
    Client = apps.get_model('tenants', 'Client')

    schemas_to_update = ['public']

    # Get all tenant schemas
    tenants = Client.objects.exclude(schema_name='public').all()
    if tenants.exists():
        schemas_to_update.extend([tenant.schema_name for tenant in tenants])

    print(f"Renaming taxontag_id to tag_id in {len(schemas_to_update)} schema(s)...")

    with connection.cursor() as cursor:
        for schema_name in schemas_to_update:
            # Check if the table exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                print(f"  Skipping {schema_name}: bims_taggroup_tags table doesn't exist")
                continue

            # Check if taxontag_id column exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                    AND column_name = 'taxontag_id'
                )
            """)
            has_taxontag_id = cursor.fetchone()[0]

            # Check if tag_id column already exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                    AND column_name = 'tag_id'
                )
            """)
            has_tag_id = cursor.fetchone()[0]

            if has_taxontag_id and not has_tag_id:
                print(f"  Updating {schema_name}...")

                # Drop old foreign key constraint to bims_taxontag if it exists
                cursor.execute(f"""
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%taxontag%'
                """)
                old_constraint = cursor.fetchone()
                if old_constraint:
                    constraint_name = old_constraint[0]
                    print(f"    Dropping old FK constraint: {constraint_name}")
                    cursor.execute(f"""
                        ALTER TABLE {schema_name}.bims_taggroup_tags
                        DROP CONSTRAINT {constraint_name}
                    """)

                # Rename column
                cursor.execute(f"""
                    ALTER TABLE {schema_name}.bims_taggroup_tags
                    RENAME COLUMN taxontag_id TO tag_id
                """)

                # Add new foreign key constraint to taggit_tag
                print(f"    Adding new FK constraint to taggit_tag")
                cursor.execute(f"""
                    ALTER TABLE {schema_name}.bims_taggroup_tags
                    ADD CONSTRAINT bims_taggroup_tags_tag_id_fkey
                    FOREIGN KEY (tag_id) REFERENCES {schema_name}.taggit_tag(id)
                    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
                """)

                print(f"  ✓ Updated {schema_name}")
            elif has_tag_id:
                print(f"  Skipping {schema_name}: tag_id column already exists")
                # Check if the correct FK constraint exists
                cursor.execute(f"""
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%tag_id%'
                """)
                fk_exists = cursor.fetchone()

                if not fk_exists:
                    # Need to add the FK constraint even though column exists
                    print(f"    Adding missing FK constraint to taggit_tag")
                    # First drop any old constraint
                    cursor.execute(f"""
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_schema = '{schema_name}'
                        AND table_name = 'bims_taggroup_tags'
                        AND constraint_type = 'FOREIGN KEY'
                        AND constraint_name LIKE '%taxontag%'
                    """)
                    old_constraint = cursor.fetchone()
                    if old_constraint:
                        cursor.execute(f"""
                            ALTER TABLE {schema_name}.bims_taggroup_tags
                            DROP CONSTRAINT {old_constraint[0]}
                        """)

                    cursor.execute(f"""
                        ALTER TABLE {schema_name}.bims_taggroup_tags
                        ADD CONSTRAINT bims_taggroup_tags_tag_id_fkey
                        FOREIGN KEY (tag_id) REFERENCES {schema_name}.taggit_tag(id)
                        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
                    """)
            else:
                print(f"  Skipping {schema_name}: taxontag_id column doesn't exist")

    print("✓ Column rename completed!")


def reverse_rename_column(apps, schema_editor):
    """
    Reverse the rename operation.
    """
    Client = apps.get_model('tenants', 'Client')

    schemas_to_update = ['public']

    # Get all tenant schemas
    tenants = Client.objects.exclude(schema_name='public').all()
    if tenants.exists():
        schemas_to_update.extend([tenant.schema_name for tenant in tenants])

    print(f"Reversing: Renaming tag_id back to taxontag_id in {len(schemas_to_update)} schema(s)...")

    with connection.cursor() as cursor:
        for schema_name in schemas_to_update:
            # Check if the table exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                continue

            # Check if tag_id column exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup_tags'
                    AND column_name = 'tag_id'
                )
            """)
            has_tag_id = cursor.fetchone()[0]

            if has_tag_id:
                cursor.execute(f"""
                    ALTER TABLE {schema_name}.bims_taggroup_tags
                    RENAME COLUMN tag_id TO taxontag_id
                """)
                print(f"  ✓ Renamed tag_id back to taxontag_id in {schema_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0494_migrate_taggroup_tags_to_tenants'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rename_column_in_all_schemas, reverse_rename_column),
    ]
