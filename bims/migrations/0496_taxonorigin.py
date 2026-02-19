import django.db.models.deletion
from django.db import migrations, models


DEFAULT_ORIGINS = [
    ('alien', 'Non-Native'),
    ('indigenous', 'Native'),
    ('unknown', 'Unknown'),
    ('alien-invasive', 'Non-native: invasive'),
    ('alien-non-invasive', 'Non-native: non-invasive'),
]


def create_default_origins(apps, schema_editor):
    TaxonOrigin = apps.get_model('bims', 'TaxonOrigin')
    for order, (origin_key, category) in enumerate(DEFAULT_ORIGINS):
        TaxonOrigin.objects.get_or_create(
            origin_key=origin_key,
            defaults={'category': category, 'order': order},
        )


def migrate_origin_data(apps, schema_editor):
    TaxonOrigin = apps.get_model('bims', 'TaxonOrigin')
    origin_map = {
        obj.origin_key: obj.id
        for obj in TaxonOrigin.objects.all()
    }

    for model_name in ('Taxonomy', 'TaxonomyUpdateProposal', 'TaxonGroupTaxonomy'):
        Model = apps.get_model('bims', model_name)
        for origin_key, origin_id in origin_map.items():
            Model.objects.filter(origin_old=origin_key).update(origin_id=origin_id)


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0495_gbifpublishconfigproxy_gbifpublishproxy_and_more'),
    ]

    operations = [
        # 1. Create TaxonOrigin model
        migrations.CreateModel(
            name='TaxonOrigin',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(
                    db_index=True, editable=False, verbose_name='order')),
                ('category', models.CharField()),
                ('origin_key', models.CharField(
                    blank=True, default='', max_length=50)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Taxon Origin',
                'verbose_name_plural': 'Taxon Origins',
                'ordering': ['order'],
                'abstract': False,
            },
        ),

        # 2. Populate default TaxonOrigin records
        migrations.RunPython(
            create_default_origins,
            migrations.RunPython.noop,
        ),

        # 3a. Rename old origin CharField on Taxonomy → origin_old
        migrations.RenameField(
            model_name='taxonomy',
            old_name='origin',
            new_name='origin_old',
        ),

        # 3b. Rename old origin CharField on TaxonomyUpdateProposal → origin_old
        migrations.RenameField(
            model_name='taxonomyupdateproposal',
            old_name='origin',
            new_name='origin_old',
        ),

        # 3c. Rename old origin CharField on TaxonGroupTaxonomy → origin_old
        migrations.RenameField(
            model_name='taxongrouptaxonomy',
            old_name='origin',
            new_name='origin_old',
        ),

        # 4a. Add new origin FK on Taxonomy
        migrations.AddField(
            model_name='taxonomy',
            name='origin',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='bims.taxonorigin',
                help_text='Origin',
            ),
        ),

        # 4b. Add new origin FK on TaxonomyUpdateProposal
        migrations.AddField(
            model_name='taxonomyupdateproposal',
            name='origin',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='bims.taxonorigin',
                help_text='Origin',
            ),
        ),

        # 4c. Add new origin FK on TaxonGroupTaxonomy
        migrations.AddField(
            model_name='taxongrouptaxonomy',
            name='origin',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='bims.taxonorigin',
                help_text='Origin',
            ),
        ),

        # 5. Migrate data from old CharField to new FK
        migrations.RunPython(
            migrate_origin_data,
            migrations.RunPython.noop,
        ),

        # 6a. Remove old origin_old CharField from Taxonomy
        migrations.RemoveField(
            model_name='taxonomy',
            name='origin_old',
        ),

        # 6b. Remove old origin_old CharField from TaxonomyUpdateProposal
        migrations.RemoveField(
            model_name='taxonomyupdateproposal',
            name='origin_old',
        ),

        # 6c. Remove old origin_old CharField from TaxonGroupTaxonomy
        migrations.RemoveField(
            model_name='taxongrouptaxonomy',
            name='origin_old',
        ),
    ]
