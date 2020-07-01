# Generated by Django 2.2.12 on 2020-06-30 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0247_auto_20200630_0524'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxauploadsession',
            name='process_file',
            field=models.FileField(null=True, upload_to='taxa-file/'),
        ),
        migrations.AddField(
            model_name='taxauploadsession',
            name='progress',
            field=models.CharField(default='', max_length=200),
        ),
    ]
