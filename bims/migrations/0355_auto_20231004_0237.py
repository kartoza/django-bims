# Generated by Django 4.1.10 on 2023-10-04 02:37

from django.db import migrations


def add_order_to_record_type(apps, schema_editor):
    RecordType = apps.get_model('bims', 'RecordType')

    record_types = RecordType.objects.all()

    for i, record_type in enumerate(record_types):
        record_type.order = i
        record_type.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0354_alter_recordtype_options_recordtype_order_and_more'),
    ]

    operations = [
        migrations.RunPython(add_order_to_record_type),
    ]
