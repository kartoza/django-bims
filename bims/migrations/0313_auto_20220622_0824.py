# Generated by Django 2.2.28 on 2022-06-22 08:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0312_auto_20220620_0644'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='national_conservation_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='national_conservation_status', to='bims.IUCNStatus', verbose_name='National Conservation Status'),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='iucn_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.IUCNStatus', verbose_name='Global Red List Status (IUCN)'),
        ),
    ]