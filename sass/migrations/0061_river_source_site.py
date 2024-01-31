# Generated by Django 4.1.10 on 2023-12-19 05:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('sass', '0060_river_end_embargo_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='river',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
    ]