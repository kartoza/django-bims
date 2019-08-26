from __future__ import unicode_literals

from django.db import migrations, models


def migrate_source_reference_database(apps, schema_editor):
    SiteVisit = apps.get_model('sass', 'SiteVisit')
    SiteVisitTaxon = apps.get_model('sass', 'SiteVisitTaxon')
    DataSource = apps.get_model('bims', 'DataSource')
    DatabaseRecord = apps.get_model('bims', 'DatabaseRecord')
    SourceReferenceDatabase = apps.get_model('bims', 'SourceReferenceDatabase')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    site_visits = SiteVisit.objects.filter(
        data_source__isnull=False
    )

    data_sources = DataSource.objects.filter(
        id__in=site_visits.distinct('data_source').values('data_source')
    )

    for data_source in data_sources:
        database, created = DatabaseRecord.objects.get_or_create(
            name=data_source.name,
            description=data_source.category
        )
        reference_database, reference_created = (
            SourceReferenceDatabase.objects.get_or_create(
                source=database
            )
        )
        SiteVisitTaxon.objects.filter(
            site_visit__in=site_visits.filter(data_source=data_source)
        ).update(
            source_reference=reference_database
        )

    new_ct = ContentType.objects.get_for_model(SourceReferenceDatabase)
    SourceReferenceDatabase.objects.filter(polymorphic_ctype__isnull=True).update(
        polymorphic_ctype=new_ct)


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0043_auto_20190823_0848'),
    ]

    operations = [
        migrations.RunPython(migrate_source_reference_database),
    ]
