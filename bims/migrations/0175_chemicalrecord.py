# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-13 07:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0046_remove_sitevisit_assessor'),
        ('bims', '0174_remove_biologicalcollectionrecord_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChemicalRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('value', models.FloatField(blank=True, null=True)),
                ('chem', models.IntegerField(blank=True, null=True)),
                ('location_site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chemical_collection_record', to='bims.LocationSite')),
            ],
        ),
    ]
