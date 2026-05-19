from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0525_taxongroup_is_readonly_upstream_url_upstream_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongrouptaxonomy',
            name='upstream_taxon_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text=(
                    'ID of the corresponding taxon on the upstream BIMS instance. '
                    'Set during harvest; used to match taxa on re-harvest without '
                    'relying solely on gbif_key or canonical name.'
                ),
                max_length=100,
            ),
        ),
    ]
