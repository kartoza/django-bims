# Generated by Django 2.2.12 on 2020-10-16 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0263_auto_20201016_0208'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='show_third_party_layer',
            field=models.BooleanField(default=False, help_text='Show third party layer selector in Map screen'),
        ),
    ]