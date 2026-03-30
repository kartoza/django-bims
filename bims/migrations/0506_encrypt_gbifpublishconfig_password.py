# Encrypt GbifPublishConfig.password at rest.
#
# The encrypted field stores data as bytea (binary), not varchar.
# This migration handles both fresh installs (varchar column) and
# databases where the column was already changed to bytea.
#
# For fresh installs (varchar column):
#   - Saves plain-text passwords, converts column to bytea, re-encrypts.
# For already-converted installs (bytea column):
#   - Reads raw bytes as hex, skips already-encrypted rows, encrypts
#     any remaining plain-text rows (valid UTF-8 bytes).

import django_cryptography.fields
from django.db import migrations, models


def _migrate_passwords(apps, schema_editor):
    from django_cryptography.fields import encrypt
    from django.db import models as dj_models

    conn = schema_editor.connection

    enc_field = encrypt(dj_models.CharField(max_length=255))
    enc_field.set_attributes_from_name("password")

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'bims_gbifpublishconfig'
              AND column_name = 'password'
              AND table_schema = current_schema()
            """
        )
        meta = cursor.fetchone()

    if meta is None:
        return

    col_type = meta[0]

    if "bytea" in col_type:
        # Column is already bytea — read raw bytes safely as hex.
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, encode(password, 'hex') "
                "FROM bims_gbifpublishconfig "
                "WHERE password IS NOT NULL AND length(password) > 0"
            )
            rows = cursor.fetchall()

        for pk, hex_val in rows:
            if not hex_val:
                continue
            raw_bytes = bytes.fromhex(hex_val)

            # Already encrypted?
            try:
                enc_field.from_db_value(raw_bytes, None, conn)
                continue
            except Exception:
                pass

            # Plain-text bytes — decode and re-encrypt.
            try:
                plain_pwd = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                continue  # unrecoverable binary, skip

            encrypted = enc_field.get_db_prep_value(plain_pwd, conn, prepared=False)
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE bims_gbifpublishconfig SET password = %s WHERE id = %s",
                    [encrypted, pk],
                )

    else:
        # Column is still varchar — read plain-text passwords before changing type.
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, password FROM bims_gbifpublishconfig "
                "WHERE password IS NOT NULL AND password <> ''"
            )
            rows = cursor.fetchall()

        # Change column type. convert_to() avoids the implicit ::bytea cast
        # error that PostgreSQL raises for text → bytea.
        with conn.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE bims_gbifpublishconfig "
                "ALTER COLUMN password TYPE bytea "
                "USING convert_to(password, 'UTF8')"
            )

        # Overwrite the raw UTF-8 bytes with properly encrypted values.
        for pk, plain_pwd in rows:
            if not plain_pwd:
                continue
            encrypted = enc_field.get_db_prep_value(plain_pwd, conn, prepared=False)
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE bims_gbifpublishconfig SET password = %s WHERE id = %s",
                    [encrypted, pk],
                )


class Migration(migrations.Migration):

    dependencies = [
        ("bims", "0505_gbifpublishcontact"),
    ]

    operations = [
        # Step 1 — encrypt existing data (handles both varchar and bytea columns).
        migrations.RunPython(_migrate_passwords, migrations.RunPython.noop),

        # Step 2 — update Django's migration state; DB change already done above.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="gbifpublishconfig",
                    name="password",
                    field=django_cryptography.fields.encrypt(
                        models.CharField(
                            help_text="GBIF password for authentication (encrypted at rest).",
                            max_length=255,
                        )
                    ),
                )
            ],
        ),
    ]
