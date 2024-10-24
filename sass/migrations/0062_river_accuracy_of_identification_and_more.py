# Generated by Django 4.2.8 on 2024-02-29 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0061_river_source_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='river',
            name='accuracy_of_identification',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of identification (0-100).'),
        ),
        migrations.AddField(
            model_name='river',
            name='accuracy_of_locality',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of locality information (0-100).'),
        ),
        migrations.AddField(
            model_name='river',
            name='reliability_of_sources',
            field=models.IntegerField(default=0, help_text='Score for the reliability of the sources (0-100).'),
        ),
    ]
