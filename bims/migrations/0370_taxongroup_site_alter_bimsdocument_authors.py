# Generated by Django 4.1.10 on 2023-12-15 08:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0369_userboundary_upload_date_alter_bimsdocument_authors'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongroup',
            name='site',
            field=models.ForeignKey(blank=True, help_text='The site this taxon group is associated with.', null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='Associated Site'),
        ),
    ]
