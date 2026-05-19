from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0526_taxongrouptaxonomy_upstream_taxon_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongrouptaxonomy',
            name='last_synced_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text=(
                    'Timestamp of the last successful harvest that touched this membership. '
                    'Null means the record was never harvested (created manually or via upload).'
                ),
            ),
        ),
        migrations.AddField(
            model_name='taxongrouptaxonomy',
            name='upstream_checksum',
            field=models.CharField(
                blank=True,
                default='',
                max_length=64,
                help_text=(
                    'SHA-256 hex digest of the canonical upstream taxon payload at the time '
                    'of last harvest. If the checksum matches on re-harvest the record is '
                    'skipped, avoiding unnecessary DB writes. An empty string means no '
                    'checksum has been recorded yet.'
                ),
            ),
        ),
    ]
