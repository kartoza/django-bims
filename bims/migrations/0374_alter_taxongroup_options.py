# Generated by Django 4.2.8 on 2023-12-21 08:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0373_taxongroup_parent_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taxongroup',
            options={'ordering': ('display_order',), 'permissions': (('can_validate_taxon_group', 'Can validate taxon group'),)},
        ),
    ]
