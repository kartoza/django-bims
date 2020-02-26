# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-02-25 07:21
from __future__ import unicode_literals
from django.core.management import call_command
from django.db import migrations

fixture = 'survey_data'

def load_fixture(apps, schema_editor):
    call_command('update_fish_species_data')


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0214_load_survey_data'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
