# Generated by Django 2.2.12 on 2020-12-02 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0275_auto_20201120_0812'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='readme_download',
            field=models.FileField(blank=True, help_text='README that bundled with the downloaded occurrence data', null=True, upload_to=''),
        ),
    ]
