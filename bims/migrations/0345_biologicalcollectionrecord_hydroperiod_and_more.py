# Generated by Django 4.1.10 on 2023-08-24 07:37

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0344_alter_bimsdocument_authors_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='hydroperiod',
            field=models.CharField(blank=True, choices=[('Inundated', 'Inundated'), ('Saturated at surface', 'Saturated at surface'), ('Dry at surface', 'Dry at surface')], default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='notification',
            name='name',
            field=models.CharField(choices=[('SITE_VISIT_VALIDATION', 'Site visit is ready to be validated'), ('SITE_VALIDATION', 'Site is ready to be validated'), ('DOWNLOAD_REQUEST', 'Download request notification'), ('ACCOUNT_CREATED', 'Account created email notification'), ('SASS_CREATED', 'SASS created email notification'), ('NEW_TAXONOMY', 'New taxonomy email notification')], max_length=255, unique=True),
        ),
    ]