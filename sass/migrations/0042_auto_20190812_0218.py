# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-12 02:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sass', '0041_sasstaxon_rating_scale'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitevisit',
            name='collector',
            field=models.ForeignKey(blank=True, help_text=b'Actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sitevisit_data_collector', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='owner',
            field=models.ForeignKey(blank=True, help_text=b'Creator/owner of this data from the web', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sitevisit_owner', to=settings.AUTH_USER_MODEL),
        ),
    ]
