# Generated by Django 2.2.28 on 2022-10-05 09:01

from django.db import migrations


def update_existing_taxa(apps, schema_editor):
    Taxonomy = apps.get_model('bims', 'Taxonomy')

    try:
        taxonomy = Taxonomy.objects.all()
        taxonomy.update(validated=True)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0325_auto_20221005_0531'),
    ]

    operations = [
        migrations.RunPython(update_existing_taxa),
    ]
