# Generated by Django 2.2.28 on 2022-11-22 18:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0326_set_existing_species_to_validated'),
    ]

    operations = [
        migrations.AddField(
            model_name='iucnstatus',
            name='national',
            field=models.BooleanField(default=False),
        ),
    ]