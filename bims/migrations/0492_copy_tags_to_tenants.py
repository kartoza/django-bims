# Generated migration to copy taggit data from public schema to all tenant schemas

from django.db import migrations, connection
from django.db.models import Q


def copy_tags_to_tenants(apps, schema_editor):
    """
    Copy Tag and TaggedItem data from public schema to all tenant schemas.
    This migration is needed because we're moving taggit from SHARED_APPS to TENANT_APPS.
    """
    Client = apps.get_model('tenants', 'Client')

    # Get all tenants
    tenants = Client.objects.exclude(schema_name='public').all()

    if not tenants.exists():
        print("No tenants found to migrate tags to.")
        return

    print(f"Found {tenants.count()} tenant(s) to migrate tags to.")

    # First, get all tags from the public schema
    with connection.cursor() as cursor:
        # Fetch all tags from public schema
        cursor.execute("""
            SELECT id, name, slug
            FROM public.taggit_tag
            ORDER BY id
        """)
        public_tags = cursor.fetchall()

        if not public_tags:
            print("No tags found in public schema.")
            return

        print(f"Found {len(public_tags)} tag(s) in public schema to copy.")

        # Fetch all tagged items from public schema
        cursor.execute("""
            SELECT id, tag_id, content_type_id, object_id
            FROM public.taggit_taggeditem
            ORDER BY id
        """)
        public_tagged_items = cursor.fetchall()

        print(f"Found {len(public_tagged_items)} tagged item(s) in public schema to copy.")

    # Now copy to each tenant schema
    for tenant in tenants:
        schema_name = tenant.schema_name
        print(f"\nProcessing tenant: {tenant.name} (schema: {schema_name})")

        with connection.cursor() as cursor:
            # Check if taggit tables exist in tenant schema
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'taggit_tag'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                print(f"  Skipping {schema_name}: taggit_tag table doesn't exist yet. Run migrate_schemas first.")
                continue

            # Copy tags
            tag_id_map = {}  # Maps public tag IDs to tenant tag IDs
            tags_copied = 0
            tags_skipped = 0

            for tag_id, name, slug in public_tags:
                # Check if tag already exists in tenant schema
                cursor.execute(f"""
                    SELECT id FROM {schema_name}.taggit_tag
                    WHERE slug = %s
                """, [slug])
                existing = cursor.fetchone()

                if existing:
                    tag_id_map[tag_id] = existing[0]
                    tags_skipped += 1
                else:
                    # Insert tag into tenant schema
                    cursor.execute(f"""
                        INSERT INTO {schema_name}.taggit_tag (name, slug)
                        VALUES (%s, %s)
                        RETURNING id
                    """, [name, slug])
                    new_tag_id = cursor.fetchone()[0]
                    tag_id_map[tag_id] = new_tag_id
                    tags_copied += 1

            print(f"  Tags: {tags_copied} copied, {tags_skipped} already existed")

            # Copy tagged items
            items_copied = 0
            items_skipped = 0

            for item_id, tag_id, content_type_id, object_id in public_tagged_items:
                # Get the new tag_id for this tenant
                new_tag_id = tag_id_map.get(tag_id)

                if not new_tag_id:
                    print(f"  Warning: Could not find mapping for tag_id {tag_id}, skipping tagged item {item_id}")
                    continue

                # Check if this tagged item already exists
                cursor.execute(f"""
                    SELECT id FROM {schema_name}.taggit_taggeditem
                    WHERE tag_id = %s AND content_type_id = %s AND object_id = %s
                """, [new_tag_id, content_type_id, object_id])

                if cursor.fetchone():
                    items_skipped += 1
                else:
                    # Check if the content_type and object still exist in this tenant
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM {schema_name}.django_content_type
                            WHERE id = %s
                        )
                    """, [content_type_id])

                    if cursor.fetchone()[0]:
                        # Insert tagged item
                        cursor.execute(f"""
                            INSERT INTO {schema_name}.taggit_taggeditem
                            (tag_id, content_type_id, object_id)
                            VALUES (%s, %s, %s)
                        """, [new_tag_id, content_type_id, object_id])
                        items_copied += 1
                    else:
                        items_skipped += 1

            print(f"  Tagged items: {items_copied} copied, {items_skipped} skipped")

    print("\n✓ Tag migration completed successfully!")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - this doesn't delete data, just prints a warning.
    Data should be manually handled if needed.
    """
    print("WARNING: Reverse migration does not delete copied tag data.")
    print("If you need to clean up, you must do so manually.")


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0491_uploadtype_model'),
        ('tenants', '0001_initial'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.RunPython(copy_tags_to_tenants, reverse_migration),
    ]
