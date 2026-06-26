from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0530_harvestschedule_bims_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='enable_harvest_worms',
            field=models.BooleanField(default=False, help_text='Enable or disable Harvest from WoRMS'),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='enable_harvest_taxonworks',
            field=models.BooleanField(default=False, help_text='Enable or disable Harvest from TaxonWorks'),
        ),
    ]
