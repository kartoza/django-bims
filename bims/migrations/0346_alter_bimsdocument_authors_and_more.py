# Generated by Django 4.1.10 on 2023-08-24 08:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0345_biologicalcollectionrecord_hydroperiod_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biologicalcollectionrecord',
            name='hydroperiod',
            field=models.CharField(blank=True, choices=[('Inundated', 'Inundated'), ('Saturated at surface', 'Saturated at surface'), ('Dry at surface', 'Dry at surface')], default='', max_length=255, null=True),
        ),
    ]
