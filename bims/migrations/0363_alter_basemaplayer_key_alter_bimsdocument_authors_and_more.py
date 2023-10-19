# Generated by Django 4.1.10 on 2023-10-19 02:46

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0362_rename_abundance_type_link_biologicalcollectionrecord_abundance_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basemaplayer',
            name='key',
            field=models.CharField(blank=True, default='', help_text='Key is required if the source of the map is Bing or Stamen', max_length=256),
        ),
        migrations.AlterField(
            model_name='notification',
            name='name',
            field=models.CharField(choices=[('SITE_VISIT_VALIDATION', 'Site visit is ready to be validated'), ('SITE_VALIDATION', 'Site is ready to be validated'), ('DOWNLOAD_REQUEST', 'Download request notification'), ('ACCOUNT_CREATED', 'Account created email notification'), ('SASS_CREATED', 'SASS created email notification'), ('NEW_TAXONOMY', 'New taxonomy email notification'), ('WETLAND_ISSUE_CREATED', 'New wetland issue email notification')], max_length=255, unique=True),
        ),
    ]
