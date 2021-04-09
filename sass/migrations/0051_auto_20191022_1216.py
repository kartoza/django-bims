# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-22 12:16
from __future__ import unicode_literals

from django.db import migrations


def merge_site_visit_chem_to_chemical_record(apps, schema_editor):
    SiteVisitChem = apps.get_model('sass', 'SiteVisitChem')
    ChemicalRecord = apps.get_model('bims', 'ChemicalRecord')
    site_visit_chems = SiteVisitChem.objects.all()
    index = 0
    for site_visit_chem in site_visit_chems:
        index += 1
        print('Merging site visit chem : %s/%s' % (index, site_visit_chems.count()))
        site = site_visit_chem.site_visit.location_site
        date = site_visit_chem.site_visit.site_visit_date
        value = site_visit_chem.chem_value
        chem_unit = site_visit_chem.chem
        ChemicalRecord.objects.get_or_create(
            date = date,
            location_site = site,
            value = value,
            chem = chem_unit
        )
        site_visit_chem.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0050_auto_20191021_0931'),
        ('bims', '0150_auto_20210409_0639')
    ]

    operations = [
        migrations.RunPython(merge_site_visit_chem_to_chemical_record),
    ]
