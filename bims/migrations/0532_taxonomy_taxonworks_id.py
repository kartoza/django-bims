from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0531_sitesetting_enable_harvest_worms_taxonworks'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='taxonworks_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, verbose_name='TaxonWorks ID'),
        ),
        migrations.AddField(
            model_name='taxonomyupdateproposal',
            name='taxonworks_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, verbose_name='TaxonWorks ID'),
        ),
    ]
