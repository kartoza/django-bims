# Generated by Django 4.2.11 on 2024-08-18 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0432_sitesetting_park_layer_csv'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='minisass_token',
            field=models.CharField(blank=True, default=''),
        ),
    ]
