# Generated by Django 4.1.10 on 2023-12-06 10:06

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0368_biologicalcollectionrecord_end_embargo_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userboundary',
            name='upload_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
