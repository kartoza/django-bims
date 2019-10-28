# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-28 07:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def migrate_location_context_group(apps, schema_editor):
    LocationContext = apps.get_model('bims', 'LocationContext')
    LocationContextGroup = apps.get_model('bims', 'LocationContextGroup')

    all_context_group_keys = list(LocationContext.objects.all().values('key', 'name', 'group_key').distinct('key'))
    index = 0
    for group_data in all_context_group_keys:
        index += 1
        print('Migrate location context group %s (%s/%s)' % (group_data['key'], index, len(all_context_group_keys)))
        group, created = LocationContextGroup.objects.get_or_create(
            name=group_data['name'],
            key=group_data['key'],
            geocontext_group_key=group_data['group_key']
        )
        LocationContext.objects.filter(key=group_data['key']).update(group=group)


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0198_auto_20191028_0714'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='locationcontextgroup',
            name='title',
        ),
        migrations.AddField(
            model_name='locationcontext',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bims.LocationContextGroup'),
        ),
        migrations.AddField(
            model_name='locationcontextgroup',
            name='geocontext_group_key',
            field=models.CharField(blank=True, default=b'', help_text=b'Group key from geocontext', max_length=255),
        ),
        migrations.AlterField(
            model_name='locationcontextgroup',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.RunPython(migrate_location_context_group),
    ]
