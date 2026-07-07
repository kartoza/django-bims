from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0535_taxongroup_contributors'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='doi',
            field=models.CharField(
                blank=True,
                default='',
                help_text='DOI or download URL for the GBIF harvest that produced this record',
                max_length=512,
            ),
        ),
    ]
