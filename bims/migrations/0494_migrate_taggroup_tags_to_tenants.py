# Generated migration to copy TagGroup tags data from public schema to all tenant schemas

from django.db import migrations, connection


def migrate_taggroup_tags_to_tenants(apps, schema_editor):
    """
    Copy TagGroup and bims_taggroup_tags data from public schema to all tenant schemas.
    This migration is needed because bims_taggroup_tags references taggit.Tag,
    which is being moved from SHARED_APPS to TENANT_APPS.
    """
    Client = apps.get_model('tenants', 'Client')

    # Get all tenants
    tenants = Client.objects.exclude(schema_name='public').all()

    if not tenants.exists():
        print("No tenants found to migrate TagGroup tags to.")
        return

    print(f"Found {tenants.count()} tenant(s) to migrate TagGroup tags to.")

    # First, get all TagGroup data from the public schema
    with connection.cursor() as cursor:
        # Fetch all TagGroups from public schema
        cursor.execute("""
            SELECT id, name, colour, "order"
            FROM public.bims_taggroup
            ORDER BY id
        """)
        public_taggroups = cursor.fetchall()

        if not public_taggroups:
            print("No TagGroups found in public schema.")
            return

        print(f"Found {len(public_taggroups)} TagGroup(s) in public schema to copy.")

        # Fetch all taggroup-tag relationships from public schema
        cursor.execute("""
            SELECT id, taggroup_id, tag_id
            FROM public.bims_taggroup_tags
            ORDER BY id
        """)
        public_taggroup_tags = cursor.fetchall()

        print(f"Found {len(public_taggroup_tags)} TagGroup-Tag relationship(s) in public schema to copy.")

    # Now copy to each tenant schema
    for tenant in tenants:
        schema_name = tenant.schema_name
        print(f"\nProcessing tenant: {tenant.name} (schema: {schema_name})")

        with connection.cursor() as cursor:
            # Check if bims_taggroup table exists in tenant schema
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'bims_taggroup'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                print(f"  Skipping {schema_name}: bims_taggroup table doesn't exist yet. Run migrate_schemas first.")
                continue

            # Check if TagGroups have already been migrated to this tenant
            cursor.execute(f"""
                SELECT COUNT(*) FROM {schema_name}.bims_taggroup
            """)
            existing_taggroup_count = cursor.fetchone()[0]

            if existing_taggroup_count > 0 and existing_taggroup_count >= len(public_taggroups):
                print(f"  Skipping {schema_name}: TagGroups already migrated ({existing_taggroup_count} TagGroups found)")
                continue
            elif existing_taggroup_count > 0:
                print(f"  Found {existing_taggroup_count} existing TagGroups in {schema_name}, will merge with public TagGroups")

            # Copy TagGroups
            taggroup_id_map = {}  # Maps public taggroup IDs to tenant taggroup IDs
            taggroups_copied = 0
            taggroups_skipped = 0

            for taggroup_id, name, colour, order in public_taggroups:
                # Check if taggroup already exists in tenant schema
                cursor.execute(f"""
                    SELECT id FROM {schema_name}.bims_taggroup
                    WHERE name = %s
                """, [name])
                existing = cursor.fetchone()

                if existing:
                    taggroup_id_map[taggroup_id] = existing[0]
                    taggroups_skipped += 1
                else:
                    # Insert taggroup into tenant schema
                    cursor.execute(f"""
                        INSERT INTO {schema_name}.bims_taggroup (name, colour, "order")
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, [name, colour, order])
                    new_taggroup_id = cursor.fetchone()[0]
                    taggroup_id_map[taggroup_id] = new_taggroup_id
                    taggroups_copied += 1

            print(f"  TagGroups: {taggroups_copied} copied, {taggroups_skipped} already existed")

            # Now map tag IDs from public schema to tenant schema
            # Build a mapping of public tag slugs to tenant tag IDs
            cursor.execute(f"""
                SELECT slug, id FROM {schema_name}.taggit_tag
            """)
            tenant_tag_map = {slug: tag_id for slug, tag_id in cursor.fetchall()}

            # Get public tag IDs and their slugs
            cursor.execute("""
                SELECT id, slug FROM public.taggit_tag
            """)
            public_tag_slugs = {tag_id: slug for tag_id, slug in cursor.fetchall()}

            # Copy taggroup-tag relationships
            relationships_copied = 0
            relationships_skipped = 0
            relationships_missing_tag = 0

            for rel_id, taggroup_id, public_tag_id in public_taggroup_tags:
                # Get the new taggroup_id for this tenant
                new_taggroup_id = taggroup_id_map.get(taggroup_id)

                if not new_taggroup_id:
                    print(f"  Warning: Could not find mapping for taggroup_id {taggroup_id}, skipping relationship {rel_id}")
                    continue

                # Get the tag slug from public schema and find corresponding tenant tag
                public_tag_slug = public_tag_slugs.get(public_tag_id)
                if not public_tag_slug:
                    print(f"  Warning: Could not find slug for public tag_id {public_tag_id}, skipping relationship {rel_id}")
                    continue

                tenant_tag_id = tenant_tag_map.get(public_tag_slug)
                if not tenant_tag_id:
                    relationships_missing_tag += 1
                    continue

                # Check if this relationship already exists
                cursor.execute(f"""
                    SELECT id FROM {schema_name}.bims_taggroup_tags
                    WHERE taggroup_id = %s AND tag_id = %s
                """, [new_taggroup_id, tenant_tag_id])

                if cursor.fetchone():
                    relationships_skipped += 1
                else:
                    # Insert relationship
                    cursor.execute(f"""
                        INSERT INTO {schema_name}.bims_taggroup_tags
                        (taggroup_id, tag_id)
                        VALUES (%s, %s)
                    """, [new_taggroup_id, tenant_tag_id])
                    relationships_copied += 1

            print(f"  TagGroup-Tag relationships: {relationships_copied} copied, {relationships_skipped} skipped, {relationships_missing_tag} missing tag in tenant")

    print("\n✓ TagGroup migration completed successfully!")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - this doesn't delete data, just prints a warning.
    Data should be manually handled if needed.
    """
    print("WARNING: Reverse migration does not delete copied TagGroup data.")
    print("If you need to clean up, you must do so manually.")


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0493_copy_tags_to_tenants'),
        ('tenants', '0001_initial'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.RunPython(migrate_taggroup_tags_to_tenants, reverse_migration),
    ]
