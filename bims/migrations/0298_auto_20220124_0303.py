# Generated by Django 2.2.16 on 2022-01-24 03:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0297_auto_20211201_0633'),
    ]

    operations = [
        migrations.AddField(
            model_name='watertemperature',
            name='source_reference',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.SourceReference'),
        )
    ]
