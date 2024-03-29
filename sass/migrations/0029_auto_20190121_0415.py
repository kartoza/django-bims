# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-21 04:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sass', '0028_auto_20190118_0614'),
    ]

    operations = [
        migrations.AddField(
            model_name='sass5sheet',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sass5sheet',
            name='ready_for_validation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sass5sheet',
            name='rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sass5sheet',
            name='validated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sass5sheet',
            name='validation_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
