# Generated by Django 4.1.10 on 2023-12-19 05:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0002_alter_domain_unique'),
        ('bims', '0370_taxongroup_site_alter_bimsdocument_authors'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
        migrations.AddField(
            model_name='survey',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
    ]