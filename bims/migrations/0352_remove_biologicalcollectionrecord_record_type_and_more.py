# Generated by Django 4.1.10 on 2023-09-29 04:29

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0351_transfer_record_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='biologicalcollectionrecord',
            name='record_type',
        ),
    ]
