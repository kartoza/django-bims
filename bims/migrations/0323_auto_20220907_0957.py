# Generated by Django 2.2.28 on 2022-09-07 09:57

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0322_auto_20220902_1249'),
    ]

    operations = [
        migrations.AddField(
            model_name='biotope',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
