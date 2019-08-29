from __future__ import unicode_literals

from django.db import migrations, models


def migrate_sass_assessor_to_owner(apps, schema_editor):
    SiteVisit = apps.get_model('sass', 'SiteVisit')

    site_visits = SiteVisit.objects.filter(
        assessor__isnull=False
    )

    for site_visit in site_visits:
        site_visit.collector = site_visit.owner
        site_visit.owner = site_visit.assessor
        site_visit.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0044_migrate_data_source_sass'),
    ]

    operations = [
        migrations.RunPython(migrate_sass_assessor_to_owner),
    ]
