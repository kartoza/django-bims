# Generated by Django 4.1.10 on 2023-11-10 08:16

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0366_nonbiodiversitylayer_document_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='locationsite',
            name='documents',
        ),
    ]