# Generated by Django 2.2.16 on 2022-04-06 06:17

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0303_auto_20220330_1821'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadsession',
            name='success_notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
