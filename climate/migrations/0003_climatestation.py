from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0532_taxonomy_taxonworks_id'),
        ('climate', '0002_climate_flag'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClimateStation',
            fields=[
            ],
            options={
                'verbose_name': 'Climate Station',
                'verbose_name_plural': 'Climate Stations',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('bims.locationsite',),
        ),
    ]
