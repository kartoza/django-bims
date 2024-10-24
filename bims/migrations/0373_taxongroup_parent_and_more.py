# Generated by Django 4.2.8 on 2023-12-21 07:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0372_searchprocess_site_alter_bimsdocument_authors'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongroup',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bims.taxongroup', verbose_name='Parent'),
        ),
        migrations.AlterField(
            model_name='taxongroup',
            name='category',
            field=models.CharField(blank=True, choices=[('SPECIES_MODULE', 'Species Module'), ('SPECIES_CLASS', 'Species Class'), ('SASS_TAXON_GROUP', 'SASS Taxon Group'), ('DIVISION_GROUP', 'Division Group'), ('LEVEL_1_GROUP', 'Level 1'), ('LEVEL_2_GROUP', 'Level 2'), ('LEVEL_3_GROUP', 'Level 3')], max_length=50, verbose_name='Taxonomic Group Category'),
        ),
    ]
