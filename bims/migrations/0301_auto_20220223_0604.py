# Generated by Django 2.2.16 on 2022-02-23 06:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0300_auto_20220127_0253'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteimage',
            name='owner',
            field=models.ForeignKey(blank=True, help_text='Owner of the data (Optional)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_image_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='siteimage',
            name='uploader',
            field=models.ForeignKey(blank=True, help_text='User who uploaded the data (Optional)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_image_uploader', to=settings.AUTH_USER_MODEL),
        ),
    ]
