# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-14 02:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0105_biotope_biotope_component'),
        ('sass', '0016_delete_old_model_from_the_state'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteVisitBiotopeTaxon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('biotope', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.Biotope')),
                ('site_visit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sass.SiteVisit')),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bims.Taxonomy')),
            ],
        ),
        migrations.CreateModel(
            name='TaxonAbundance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abc', models.CharField(blank=True, max_length=10, null=True)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
                ('display_order', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='sitevisitbiotopetaxon',
            name='taxon_abundance',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sass.TaxonAbundance'),
        ),
    ]
