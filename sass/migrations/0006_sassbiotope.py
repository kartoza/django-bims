# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-09 11:42
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0005_sitevisit_location_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='SassBiotope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('display_order', models.FloatField(blank=True, null=True)),
                ('biotope_form', models.CharField(blank=True, choices=[(b'0', b'0'), (b'1', b'1'), (b'2', b'2')], max_length=2)),
                ('additional_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True)),
            ],
        ),
    ]
