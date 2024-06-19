# Generated by Django 4.2.8 on 2024-06-18 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0407_taxongroup_occurrence_upload_template_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='hierarchical_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Hierarchical Data'),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='rank',
            field=models.CharField(blank=True, choices=[('SUBSPECIES', 'Sub Species'), ('SPECIES', 'Species'), ('GENUS', 'Genus'), ('SUBGENUS', 'Sub Genus'), ('FAMILY', 'Family'), ('SUPERFAMILY', 'Super Family'), ('ORDER', 'Order'), ('CLASS', 'Class'), ('SUBCLASS', 'Sub Class'), ('PHYLUM', 'Phylum'), ('SUBPHYLUM', 'SubPhylum'), ('KINGDOM', 'Kingdom'), ('DOMAIN', 'Domain'), ('SUBORDER', 'Sub Order'), ('INFRAORDER', 'Infra Order'), ('SUBFAMILY', 'Sub Family'), ('VARIETY', 'Variety'), ('FORMA', 'Forma'), ('TRIBE', 'Tribe'), ('SUBTRIBE', 'Sub Tribe')], max_length=50, verbose_name='Taxonomic Rank'),
        ),
    ]
