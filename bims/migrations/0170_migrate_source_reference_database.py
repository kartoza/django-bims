from __future__ import unicode_literals

from django.db import migrations, models


def migrate_source_reference_database(apps, schema_editor):
    BiologicalCollectionRecord = apps.get_model('bims', 'BiologicalCollectionRecord')
    SourceReferenceDatabase = apps.get_model('bims', 'SourceReferenceDatabase')
    DatabaseRecord = apps.get_model('bims', 'DatabaseRecord')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    collections = BiologicalCollectionRecord.objects.filter(
        reference__isnull=False,
        source_reference__isnull=True
    ).exclude(reference='')
    collection_with_database = collections.filter(
        models.Q(reference__icontains='database') |
        models.Q(reference_category__icontains='database')
    )
    for collection in collection_with_database:
        database, created = DatabaseRecord.objects.get_or_create(
            name=collection.reference
        )
        reference_database, reference_created = (
            SourceReferenceDatabase.objects.get_or_create(
                source=database
            )
        )
        collection.source_reference = reference_database
        collection.save()

    new_ct = ContentType.objects.get_for_model(SourceReferenceDatabase)
    SourceReferenceDatabase.objects.filter(polymorphic_ctype__isnull=True).update(
        polymorphic_ctype=new_ct)


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0160_auto_20190823_0848'),
    ]

    operations = [
        migrations.RunPython(migrate_source_reference_database),
    ]
