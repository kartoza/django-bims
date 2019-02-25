# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-05 05:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sass', '0029_auto_20190121_0415'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sass5record',
            name='sass_sheet',
        ),
        migrations.RemoveField(
            model_name='sass5record',
            name='taxonomy',
        ),
        migrations.RemoveField(
            model_name='sass5sheet',
            name='location_site',
        ),
        migrations.RemoveField(
            model_name='sass5sheet',
            name='owner',
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sitevisit_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='assessor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sitevisit_assessor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='SASS5Record',
        ),
        migrations.DeleteModel(
            name='SASS5Sheet',
        ),
    ]
