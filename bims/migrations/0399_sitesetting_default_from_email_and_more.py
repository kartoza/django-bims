# Generated by Django 4.2.8 on 2024-05-01 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0398_sitesetting_enable_ecosystem_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='default_from_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='resend_api_key',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='rank',
            field=models.CharField(blank=True, choices=[('SUBSPECIES', 'Sub Species'), ('SPECIES', 'Species'), ('GENUS', 'Genus'), ('FAMILY', 'Family'), ('SUPERFAMILY', 'Super Family'), ('ORDER', 'Order'), ('CLASS', 'Class'), ('SUBCLASS', 'Sub Class'), ('PHYLUM', 'Phylum'), ('SUBPHYLUM', 'SubPhylum'), ('KINGDOM', 'Kingdom'), ('DOMAIN', 'Domain'), ('LIFE', 'Life'), ('CULTIVAR_GROUP', 'Cultivar Group'), ('SUBORDER', 'Sub Order'), ('INFRAORDER', 'Infra Order'), ('SUBFAMILY', 'Sub Family'), ('VARIETY', 'Variety'), ('FORMA', 'Forma')], max_length=50, verbose_name='Taxonomic Rank'),
        ),
    ]
