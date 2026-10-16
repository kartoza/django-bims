from django.db import migrations


class Migration(migrations.Migration):
    """Some deployments recorded 0551 before it added gbif_metadata_file,
    leaving the column missing. Add it only if absent."""

    dependencies = [
        ('bims', '0553_delete_climatedata'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE bims_sourcereference '
                'ADD COLUMN IF NOT EXISTS gbif_metadata_file varchar(100) NULL',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
