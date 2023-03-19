# Generated by Django 2.2.28 on 2023-03-19 07:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0332_auto_20230306_0504'),
    ]

    operations = [
        migrations.AddField(
            model_name='nonbiodiversitylayer',
            name='csv_attribute',
            field=models.CharField(blank=True, help_text='Column name in the csv that will be used to filter csv_file.', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='nonbiodiversitylayer',
            name='csv_file',
            field=models.FileField(blank=True, help_text='A CSV file that will be filtered and downloaded based on matching values between "layer_csv_attribute" and "csv_attribute". This will also show the download button in the attribute data panel.', null=True, upload_to='non_biodiversity_layer_csv_file'),
        ),
        migrations.AddField(
            model_name='nonbiodiversitylayer',
            name='layer_csv_attribute',
            field=models.CharField(blank=True, help_text='Attribute in the layer that will be used to filter csv_file.', max_length=128, null=True),
        ),
    ]
