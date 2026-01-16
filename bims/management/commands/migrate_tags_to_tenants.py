import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django_tenants.utils import get_tenant_model


class Command(BaseCommand):
    help = (
        "Copy taggit tags/tagged items and TagGroup tags from public schema "
        "to tenant schemas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-s",
            "--schema-name",
            dest="schema_names",
            action="append",
            help="Limit to specific tenant schema(s). Can be passed multiple times.",
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help="Process all tenants (default if no schema is provided).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        schema_names = options.get("schema_names") or []
        dry_run = options.get("dry_run", False)
        all_tenants = options.get("all_tenants", False)

        if schema_names and all_tenants:
            raise CommandError("Use either --schema-name or --all-tenants, not both.")

        for schema_name in schema_names:
            self._validate_schema_name(schema_name)

        tenants = self._get_tenants(schema_names)
        if not tenants:
            self.stdout.write(self.style.WARNING("No tenants found to process."))
            return

        self._print_mode(dry_run, tenants)

        public_data = self._load_public_data()
        if not public_data["public_tags"]:
            self.stdout.write(self.style.WARNING("No tags found in public schema."))
        if not public_data["public_taggroups"]:
            self.stdout.write(self.style.WARNING("No TagGroups found in public schema."))

        for tenant in tenants:
            label = f"{tenant.name} (schema: {tenant.schema_name})"
            self.stdout.write(f"Processing {label}")

            if dry_run:
                self._process_tenant(tenant, public_data, dry_run=True)
            else:
                with transaction.atomic():
                    self._process_tenant(tenant, public_data, dry_run=False)

        self.stdout.write(self.style.SUCCESS("Tag migration command completed."))

    def _validate_schema_name(self, schema_name):
        if not re.match(r"^[A-Za-z0-9_]+$", schema_name or ""):
            raise CommandError(f"Invalid schema name: {schema_name}")

    def _get_tenants(self, schema_names):
        Tenant = get_tenant_model()
        tenants = Tenant.objects.exclude(schema_name="public")
        if schema_names:
            tenants = tenants.filter(schema_name__in=schema_names)
            missing = set(schema_names) - set(tenants.values_list("schema_name", flat=True))
            if missing:
                raise CommandError(f"Tenant schema(s) not found: {', '.join(sorted(missing))}")
        return list(tenants.order_by("schema_name"))

    def _print_mode(self, dry_run, tenants):
        mode = "DRY RUN" if dry_run else "LIVE RUN"
        self.stdout.write(f"{mode}: {len(tenants)} tenant(s) selected.")

    def _load_public_data(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, slug
                FROM public.taggit_tag
                ORDER BY id
            """)
            public_tags = cursor.fetchall()

            cursor.execute("""
                SELECT id, tag_id, content_type_id, object_id
                FROM public.taggit_taggeditem
                ORDER BY id
            """)
            public_tagged_items = cursor.fetchall()

            cursor.execute("""
                SELECT id, name, colour, "order"
                FROM public.bims_taggroup
                ORDER BY id
            """)
            public_taggroups = cursor.fetchall()

            cursor.execute("""
                SELECT id, taggroup_id, tag_id
                FROM public.bims_taggroup_tags
                ORDER BY id
            """)
            public_taggroup_tags = cursor.fetchall()

            cursor.execute("""
                SELECT id FROM public.django_content_type
            """)
            public_content_types = {row[0] for row in cursor.fetchall()}

        return {
            "public_tags": public_tags,
            "public_tagged_items": public_tagged_items,
            "public_taggroups": public_taggroups,
            "public_taggroup_tags": public_taggroup_tags,
            "public_content_types": public_content_types,
        }

    def _process_tenant(self, tenant, public_data, dry_run):
        schema_name = tenant.schema_name
        with connection.cursor() as cursor:
            self._copy_tags_to_tenant(
                cursor,
                schema_name,
                public_data["public_tags"],
                public_data["public_tagged_items"],
                public_data["public_content_types"],
                dry_run,
            )
            self._migrate_taggroup_tags_to_tenant(
                cursor,
                schema_name,
                public_data["public_taggroups"],
                public_data["public_taggroup_tags"],
                public_data["public_tags"],
                dry_run,
            )

    def _table_exists(self, cursor, schema_name, table_name):
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name = %s
            )
            """,
            [schema_name, table_name],
        )
        return cursor.fetchone()[0]

    def _ensure_taggit_tables(self, cursor, schema_name, dry_run):
        tag_table_exists = self._table_exists(cursor, schema_name, "taggit_tag")
        tagged_table_exists = self._table_exists(cursor, schema_name, "taggit_taggeditem")

        if tag_table_exists and tagged_table_exists:
            return True

        if dry_run:
            missing = []
            if not tag_table_exists:
                missing.append("taggit_tag")
            if not tagged_table_exists:
                missing.append("taggit_taggeditem")
            self.stdout.write(self.style.WARNING(
                f"[DRY RUN] Would create missing tables in {schema_name}: {', '.join(missing)}"
            ))
            return False

        if not tag_table_exists:
            cursor.execute(f"""
                CREATE TABLE {schema_name}.taggit_tag
                (LIKE public.taggit_tag INCLUDING ALL)
            """)
        if not tagged_table_exists:
            cursor.execute(f"""
                CREATE TABLE {schema_name}.taggit_taggeditem
                (LIKE public.taggit_taggeditem INCLUDING ALL)
            """)
            cursor.execute(f"""
                ALTER TABLE {schema_name}.taggit_taggeditem
                ADD CONSTRAINT taggit_taggeditem_tag_id_fkey
                FOREIGN KEY (tag_id) REFERENCES {schema_name}.taggit_tag(id)
                ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
            """)

        self.stdout.write(self.style.SUCCESS(f"Created missing taggit tables in {schema_name}."))
        return True

    def _copy_tags_to_tenant(
        self,
        cursor,
        schema_name,
        public_tags,
        public_tagged_items,
        public_content_types,
        dry_run,
    ):
        if not public_tags:
            return

        tables_ready = self._ensure_taggit_tables(cursor, schema_name, dry_run)
        can_query_taggit = tables_ready

        existing_tag_count = 0
        tenant_tags_by_slug = {}
        tenant_tags_by_name = {}
        if can_query_taggit:
            cursor.execute(f"""
                SELECT id, name, slug FROM {schema_name}.taggit_tag
            """)
            for tag_id, name, slug in cursor.fetchall():
                tenant_tags_by_slug[slug] = tag_id
                tenant_tags_by_name[name] = tag_id
            existing_tag_count = len(tenant_tags_by_slug)

        if existing_tag_count > 0 and existing_tag_count >= len(public_tags):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping {schema_name}: Tags already migrated ({existing_tag_count} tags found)."
                )
            )
            return
        if existing_tag_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {existing_tag_count} existing tags in {schema_name}, will merge."
                )
            )

        tag_id_map = {}
        tags_copied = 0
        tags_skipped = 0

        for tag_id, name, slug in public_tags:
            existing_id = tenant_tags_by_slug.get(slug) or tenant_tags_by_name.get(name)
            if existing_id:
                tag_id_map[tag_id] = existing_id
                tags_skipped += 1
                continue

            if dry_run:
                tags_copied += 1
                continue

            cursor.execute(f"""
                INSERT INTO {schema_name}.taggit_tag (name, slug)
                VALUES (%s, %s)
                RETURNING id
            """, [name, slug])
            new_tag_id = cursor.fetchone()[0]
            tenant_tags_by_slug[slug] = new_tag_id
            tenant_tags_by_name[name] = new_tag_id
            tag_id_map[tag_id] = new_tag_id
            tags_copied += 1

        dry_prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{dry_prefix}Tags: {tags_copied} copied, {tags_skipped} already existed."
            )
        )

        if not public_tagged_items:
            return

        items_copied = 0
        items_skipped = 0
        items_missing_tag = 0

        public_tag_slugs = {tag_id: slug for tag_id, _, slug in public_tags}

        for item_id, tag_id, content_type_id, object_id in public_tagged_items:
            if content_type_id not in public_content_types:
                items_skipped += 1
                continue

            if dry_run:
                public_tag_slug = public_tag_slugs.get(tag_id)
                if not public_tag_slug:
                    items_missing_tag += 1
                    continue
                tenant_tag_id = tenant_tags_by_slug.get(public_tag_slug)
                if not tenant_tag_id:
                    items_copied += 1
                    continue

                if can_query_taggit:
                    cursor.execute(
                        f"""
                        SELECT 1
                        FROM {schema_name}.taggit_taggeditem ti
                        JOIN {schema_name}.taggit_tag t ON t.id = ti.tag_id
                        WHERE t.slug = %s AND ti.content_type_id = %s AND ti.object_id = %s
                        """,
                        [public_tag_slug, content_type_id, object_id],
                    )
                    if cursor.fetchone():
                        items_skipped += 1
                    else:
                        items_copied += 1
                else:
                    items_copied += 1
                continue

            new_tag_id = tag_id_map.get(tag_id)
            if not new_tag_id:
                items_missing_tag += 1
                continue

            cursor.execute(f"""
                SELECT id FROM {schema_name}.taggit_taggeditem
                WHERE tag_id = %s AND content_type_id = %s AND object_id = %s
            """, [new_tag_id, content_type_id, object_id])

            if cursor.fetchone():
                items_skipped += 1
            else:
                cursor.execute(f"""
                    INSERT INTO {schema_name}.taggit_taggeditem
                    (tag_id, content_type_id, object_id)
                    VALUES (%s, %s, %s)
                """, [new_tag_id, content_type_id, object_id])
                items_copied += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{dry_prefix}Tagged items: {items_copied} copied, {items_skipped} skipped, "
                f"{items_missing_tag} missing tag."
            )
        )

    def _migrate_taggroup_tags_to_tenant(
        self,
        cursor,
        schema_name,
        public_taggroups,
        public_taggroup_tags,
        public_tags,
        dry_run,
    ):
        if not public_taggroups:
            return

        if not self._table_exists(cursor, schema_name, "bims_taggroup"):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping {schema_name}: bims_taggroup table doesn't exist yet."
                )
            )
            return

        if not self._table_exists(cursor, schema_name, "taggit_tag"):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping {schema_name}: taggit_tag table doesn't exist yet."
                )
            )
            return

        cursor.execute(f"""
            SELECT id, name FROM {schema_name}.bims_taggroup
        """)
        tenant_taggroup_by_name = {name: taggroup_id for taggroup_id, name in cursor.fetchall()}
        existing_taggroup_count = len(tenant_taggroup_by_name)

        if existing_taggroup_count > 0 and existing_taggroup_count >= len(public_taggroups):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping {schema_name}: TagGroups already migrated "
                    f"({existing_taggroup_count} found)."
                )
            )
            return
        if existing_taggroup_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {existing_taggroup_count} existing TagGroups in {schema_name}, will merge."
                )
            )

        taggroup_id_map = {}
        taggroups_copied = 0
        taggroups_skipped = 0
        public_taggroup_names = {taggroup_id: name for taggroup_id, name, _, _ in public_taggroups}

        for taggroup_id, name, colour, order in public_taggroups:
            existing_id = tenant_taggroup_by_name.get(name)
            if existing_id:
                taggroup_id_map[taggroup_id] = existing_id
                taggroups_skipped += 1
                continue

            if dry_run:
                taggroups_copied += 1
                continue

            cursor.execute(f"""
                INSERT INTO {schema_name}.bims_taggroup (name, colour, "order")
                VALUES (%s, %s, %s)
                RETURNING id
            """, [name, colour, order])
            new_taggroup_id = cursor.fetchone()[0]
            tenant_taggroup_by_name[name] = new_taggroup_id
            taggroup_id_map[taggroup_id] = new_taggroup_id
            taggroups_copied += 1

        dry_prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{dry_prefix}TagGroups: {taggroups_copied} copied, {taggroups_skipped} already existed."
            )
        )

        if not public_taggroup_tags:
            return

        cursor.execute(f"""
            SELECT slug, id FROM {schema_name}.taggit_tag
        """)
        tenant_tag_map = {slug: tag_id for slug, tag_id in cursor.fetchall()}
        public_tag_slugs = {tag_id: slug for tag_id, _, slug in public_tags}

        relationships_copied = 0
        relationships_skipped = 0
        relationships_missing_tag = 0

        for rel_id, taggroup_id, public_tag_id in public_taggroup_tags:
            taggroup_name = public_taggroup_names.get(taggroup_id)
            if not taggroup_name:
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Could not find name for taggroup_id {taggroup_id}, "
                        f"skipping relationship {rel_id}."
                    )
                )
                continue

            public_tag_slug = public_tag_slugs.get(public_tag_id)
            if not public_tag_slug:
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Could not find slug for public tag_id {public_tag_id}, "
                        f"skipping relationship {rel_id}."
                    )
                )
                continue

            tenant_tag_id = tenant_tag_map.get(public_tag_slug)
            if not tenant_tag_id:
                relationships_missing_tag += 1
                continue

            if dry_run:
                cursor.execute(
                    f"""
                    SELECT 1
                    FROM {schema_name}.bims_taggroup_tags tt
                    JOIN {schema_name}.bims_taggroup tg ON tg.id = tt.taggroup_id
                    JOIN {schema_name}.taggit_tag t ON t.id = tt.tag_id
                    WHERE tg.name = %s AND t.slug = %s
                    """,
                    [taggroup_name, public_tag_slug],
                )
                if cursor.fetchone():
                    relationships_skipped += 1
                else:
                    relationships_copied += 1
                continue

            new_taggroup_id = taggroup_id_map.get(taggroup_id)
            if not new_taggroup_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Could not find mapping for taggroup_id {taggroup_id}, "
                        f"skipping relationship {rel_id}."
                    )
                )
                continue

            cursor.execute(f"""
                SELECT id FROM {schema_name}.bims_taggroup_tags
                WHERE taggroup_id = %s AND tag_id = %s
            """, [new_taggroup_id, tenant_tag_id])

            if cursor.fetchone():
                relationships_skipped += 1
            else:
                cursor.execute(f"""
                    INSERT INTO {schema_name}.bims_taggroup_tags
                    (taggroup_id, tag_id)
                    VALUES (%s, %s)
                """, [new_taggroup_id, tenant_tag_id])
                relationships_copied += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{dry_prefix}TagGroup-Tag relationships: {relationships_copied} copied, "
                f"{relationships_skipped} skipped, {relationships_missing_tag} missing tag."
            )
        )
