# Generated by Django 2.2.16 on 2022-04-26 07:22

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0304_auto_20220406_0617'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcereference',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
