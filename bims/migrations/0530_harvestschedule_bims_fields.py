from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0529_merge_20260603_0743'),
    ]

    operations = [
        migrations.AddField(
            model_name='harvestschedule',
            name='category',
            field=models.CharField(
                choices=[('gbif', 'GBIF'), ('bims', 'BIMS Instance')],
                default='gbif',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='harvestschedule',
            name='bims_config',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='BIMS instance config: base_url, remote_group_id, remote_group_name',
            ),
        ),
    ]
