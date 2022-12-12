# Generated by Django 2.2.28 on 2022-11-24 08:07

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0326_set_existing_species_to_validated'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='mobile',
            field=models.BooleanField(default=False, help_text='Whether this data is created form mobile app or not'),
        ),
        migrations.AlterField(
            model_name='iucnstatus',
            name='category',
            field=models.CharField(blank=True, choices=[('LC', 'Least concern'), ('NT', 'Near threatened'), ('VU', 'Vulnerable'), ('EN', 'Endangered'), ('CR', 'Critically endangered'), ('EW', 'Extinct in the wild'), ('EX', 'Extinct'), ('DD', 'Data deficient'), ('NE', 'Not evaluated'), ('RE', 'Regionally Extinct'), ('CE', 'Critically Endangered, Possibly Extinct'), ('CA', 'Critically Rare'), ('RA', 'Rare'), ('DI', 'Data Deficient - Insufficient Information'), ('DT', 'Data Deficient - Taxonomically Problematic')], default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='taxongroup',
            name='chart_data',
            field=models.CharField(blank=True, choices=[('conservation status', 'Conservation Status'), ('division', 'Division'), ('sass', 'SASS'), ('origin', 'Origin'), ('endemism', 'Endemism')], default='', help_text='Data to display on chart', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='rank',
            field=models.CharField(blank=True, choices=[('SUBSPECIES', 'Sub Species'), ('SPECIES', 'Species'), ('GENUS', 'Genus'), ('FAMILY', 'Family'), ('SUPERFAMILY', 'Super Family'), ('ORDER', 'Order'), ('CLASS', 'Class'), ('SUBCLASS', 'Sub Class'), ('PHYLUM', 'Phylum'), ('KINGDOM', 'Kingdom'), ('DOMAIN', 'Domain'), ('LIFE', 'Life'), ('CULTIVAR_GROUP', 'Cultivar Group'), ('SUBORDER', 'Sub Order'), ('INFRAORDER', 'Infra Order'), ('SUBFAMILY', 'Sub Family'), ('VARIETY', 'Variety')], max_length=50, verbose_name='Taxonomic Rank'),
        ),
    ]
