# Generated by Django 4.2.8 on 2024-06-05 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0403_sitesetting_homepage_redirect_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='geoserver_location_site_layer',
            field=models.CharField(blank=True, default='bims:location_site_view', max_length=128),
        ),
    ]
