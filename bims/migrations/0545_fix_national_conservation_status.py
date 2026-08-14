from django.db import migrations


def fix_national_conservation_status(apps, schema_editor):
    Taxonomy = apps.get_model('bims', 'Taxonomy')
    IUCNStatus = apps.get_model('bims', 'IUCNStatus')

    national_by_category = {
        s.category: s
        for s in IUCNStatus.objects.filter(national=True)
    }
    if not national_by_category:
        return

    affected = Taxonomy.objects.filter(
        national_conservation_status__isnull=False,
        national_conservation_status__national=False,
    ).select_related('national_conservation_status')

    for taxon in affected.iterator():
        replacement = national_by_category.get(
            taxon.national_conservation_status.category
        )
        if replacement is None:
            continue
        taxon.national_conservation_status = replacement
        taxon.save(update_fields=['national_conservation_status'])


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0544_taxongroup_taxonworks_base_url_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_national_conservation_status,
            migrations.RunPython.noop,
        ),
    ]
