# Generated by Django 4.2.11 on 2024-08-07 12:31

from django.db import migrations


def create_groups(apps, schema_editor):
    try:
        Group = apps.get_model('auth', 'Group')
        group_names = ['SensitiveDataGroup', 'PrivateDataGroup']
        for group_name in group_names:
            if not Group.objects.filter(name=group_name).exists():
                Group.objects.create(name=group_name)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0430_invasion_taxonomy_invasion_and_more'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
