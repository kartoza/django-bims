# Generated by Django 4.2.8 on 2024-04-26 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0397_alter_biologicalcollectionrecord_survey'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='enable_ecosystem_type',
            field=models.BooleanField(default=False),
        ),
    ]
