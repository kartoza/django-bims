from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0524_taxonomy_sanbi_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongroup',
            name='is_readonly',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'When enabled, species in this taxon group cannot be edited '
                    'locally. The group is managed by harvesting from an upstream '
                    'BIMS instance.'
                ),
            ),
        ),
        migrations.AddField(
            model_name='taxongroup',
            name='upstream_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='Base URL of the upstream BIMS instance this group is harvested from.',
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name='taxongroup',
            name='upstream_id',
            field=models.CharField(
                blank=True,
                default='',
                help_text='ID of the taxon group on the upstream BIMS instance.',
                max_length=100,
            ),
        ),
    ]
