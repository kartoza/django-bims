#!/usr/bin/env python
"""
Script to migrate taggit from SHARED_APPS to TENANT_APPS.

This script:
1. Creates taggit tables in tenant schemas
2. Copies tag data from public schema to all tenant schemas

Usage:
    python manage.py shell < scripts/migrate_taggit_to_tenants.py

Or within Django shell:
    exec(open('scripts/migrate_taggit_to_tenants.py').read())
"""

from django.db import connection
from tenants.models import Client

def migrate_taggit_to_tenants():
    """Migrate taggit tables and data from public schema to all tenant schemas."""

    # Get all tenants (excluding public)
    tenants = Client.objects.exclude(schema_name='public').all()

    if not tenants.exists():
        print("No tenants found.")
        return

    print(f"Found {tenants.count()} tenant(s) to process\n")

    # Get tags and tagged items from public schema
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, slug FROM public.taggit_tag ORDER BY id")
        public_tags = cursor.fetchall()

        cursor.execute("SELECT id, tag_id, content_type_id, object_id FROM public.taggit_taggeditem ORDER BY id")
        public_tagged_items = cursor.fetchall()

    print(f"Source data: {len(public_tags)} tags, {len(public_tagged_items)} tagged items\n")

    # Process each tenant
    for tenant in tenants:
        schema = tenant.schema_name
        print(f"Processing: {tenant.name} (schema: {schema})")

        with connection.cursor() as cursor:
            # Check if taggit_tag table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_tables
                    WHERE schemaname = %s
                    AND tablename = 'taggit_tag'
                )
            """, [schema])

            table_exists = cursor.fetchone()[0]

            if not table_exists:
                # Create tables
                print("  Creating taggit tables...")

                try:
                    cursor.execute(f"""
                        CREATE TABLE {schema}.taggit_tag (
                            LIKE public.taggit_tag INCLUDING ALL
                        );
                    """)

                    cursor.execute(f"""
                        CREATE TABLE {schema}.taggit_taggeditem (
                            LIKE public.taggit_taggeditem INCLUDING ALL
                        );
                    """)

                    # Add foreign key constraints
                    cursor.execute(f"""
                        ALTER TABLE {schema}.taggit_taggeditem
                        ADD CONSTRAINT taggit_taggeditem_tag_id_fkey
                        FOREIGN KEY (tag_id) REFERENCES {schema}.taggit_tag(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    """)

                    cursor.execute(f"""
                        ALTER TABLE {schema}.taggit_taggeditem
                        ADD CONSTRAINT taggit_taggeditem_content_type_id_fkey
                        FOREIGN KEY (content_type_id) REFERENCES {schema}.django_content_type(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    """)

                    print("  ✓ Tables created")

                except Exception as e:
                    print(f"  ⚠ Error creating tables: {e}")
                    print(f"  Skipping tenant {schema}\n")
                    continue

            # Copy tags
            tag_map = {}
            tags_copied = 0

            for tag_id, name, slug in public_tags:
                cursor.execute(f"SELECT id FROM {schema}.taggit_tag WHERE slug = %s", [slug])
                existing = cursor.fetchone()

                if not existing:
                    cursor.execute(
                        f"INSERT INTO {schema}.taggit_tag (name, slug) VALUES (%s, %s) RETURNING id",
                        [name, slug]
                    )
                    tag_map[tag_id] = cursor.fetchone()[0]
                    tags_copied += 1
                else:
                    tag_map[tag_id] = existing[0]

            # Copy tagged items
            items_copied = 0

            for item_id, tag_id, content_type_id, object_id in public_tagged_items:
                new_tag_id = tag_map.get(tag_id)
                if not new_tag_id:
                    continue

                try:
                    # Use INSERT ... ON CONFLICT DO NOTHING to avoid duplicate errors
                    cursor.execute(f"""
                        INSERT INTO {schema}.taggit_taggeditem (tag_id, content_type_id, object_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, [new_tag_id, content_type_id, object_id])

                    if cursor.rowcount > 0:
                        items_copied += 1
                except Exception:
                    # Skip items that reference non-existent content types or objects
                    pass

            # Get final counts
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.taggit_tag")
            final_tag_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {schema}.taggit_taggeditem")
            final_item_count = cursor.fetchone()[0]

            print(f"  ✓ Tags: {tags_copied} new, {final_tag_count} total")
            print(f"  ✓ Tagged items: {items_copied} new, {final_item_count} total\n")

    print("✓ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Mark taggit migrations as applied for each tenant:")
    print("   python manage.py tenant_command migrate taggit --fake")
    print("2. Verify data in tenant schemas:")
    print("   python manage.py tenant_command shell --schema=<tenant>")


if __name__ == '__main__':
    migrate_taggit_to_tenants()
else:
    # Auto-run when imported/exec'd
    migrate_taggit_to_tenants()
