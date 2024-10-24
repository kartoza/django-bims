# Generated by Django 2.2.28 on 2023-04-12 07:45

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0333_auto_20230319_0705'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='pesticide_quaternary_data_file',
            field=models.FileField(blank=True, help_text='File containing pesticide data per quaternary. If not provided, the pesticide dashboard will be unavailable.', null=True, upload_to=''),
        ),
    ]
