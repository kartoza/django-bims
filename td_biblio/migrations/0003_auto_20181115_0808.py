# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-15 08:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('td_biblio', '0002_auto_20181115_0808'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-publication_date',), 'permissions': (('can_add_bibliograpy_entry', 'Can Add Bibliography Entry'),), 'verbose_name': 'Entry', 'verbose_name_plural': 'Entries'},
        ),
    ]
