from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0527_remove_harvestsession_source_site'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gbifpublishconfig',
            name='license_url',
        ),
        migrations.AddField(
            model_name='gbifpublishconfig',
            name='license',
            field=models.ForeignKey(
                blank=True,
                help_text='License for the dataset (default: CC BY 4.0 - Attribution).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='gbif_configs',
                to='bims.licence',
            ),
        ),
    ]
