# Generated by Django 4.2.8 on 2024-05-18 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0402_sitesetting_cites_token_api'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='homepage_redirect_url',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]