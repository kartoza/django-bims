# Generated by Django 4.1.10 on 2023-10-19 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims_theme', '0009_auto_20230712_0745'),
    ]

    operations = [
        migrations.AddField(
            model_name='customtheme',
            name='navbar_logo',
            field=models.ImageField(blank=True, null=True, upload_to='navbar_site_logo'),
        ),
    ]