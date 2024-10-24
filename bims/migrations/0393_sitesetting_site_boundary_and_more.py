# Generated by Django 4.2.8 on 2024-03-11 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('bims', '0392_nonbiodiversitylayer_additional_sites_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='site_boundary',
            field=models.ForeignKey(blank=True, help_text='Boundary used for checking if the site is within the correct boundary', null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.boundary'),
        ),
        migrations.AlterField(
            model_name='nonbiodiversitylayer',
            name='source_site',
            field=models.ForeignKey(blank=True, help_text='The site this record is first associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Source Site'),
        ),
    ]
