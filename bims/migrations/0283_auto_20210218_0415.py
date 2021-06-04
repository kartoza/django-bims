# Generated by Django 2.2.12 on 2021-02-18 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0282_merge_20210218_0331'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='endemism',
            options={'ordering': ['display_order']},
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='iucn_api_key',
            field=models.CharField(default='', help_text='Token key for IUCN api', max_length=255),
        ),
    ]