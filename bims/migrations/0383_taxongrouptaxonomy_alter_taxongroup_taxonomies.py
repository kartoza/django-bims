# Generated by Django 4.2.8 on 2024-02-07 17:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0382_alter_bimsdocument_authors'),
    ]

    state_operations = [
        migrations.CreateModel(
            name='TaxonGroupTaxonomy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_validated', models.BooleanField(default=False)),
                ('taxongroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bims.taxongroup')),
                ('taxonomy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bims.taxonomy')),
            ],
            options={
                'unique_together': {('taxongroup', 'taxonomy')},
            },
        ),
        migrations.AlterModelTable(
            name='taxongrouptaxonomy',
            table='bims_taxongroup_taxonomies'
        ),
        migrations.AlterField(
            model_name='taxongroup',
            name='taxonomies',
            field=models.ManyToManyField(blank=True, through='bims.TaxonGroupTaxonomy', to='bims.taxonomy'),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations
        ),
        migrations.AddField(
            model_name='TaxonGroupTaxonomy',
            name='is_validated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelTable(
            name='taxongrouptaxonomy',
            table=None,
        ),
    ]
