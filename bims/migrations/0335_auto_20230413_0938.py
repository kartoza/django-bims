# Generated by Django 2.2.28 on 2023-04-13 09:38

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0334_auto_20230412_0745'),
    ]

    operations = [
        migrations.AddField(
            model_name='nonbiodiversitylayer',
            name='enable_styles_selection',
            field=models.BooleanField(default=False, help_text='Check this box to show the styles selection in the layer selector.', verbose_name='Enable styles selection'),
        ),
    ]