# Generated by Django 4.1.10 on 2023-08-23 09:07

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0343_locationsite_ecosystem_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('SITE_VISIT_VALIDATION', 'Site visit is ready to be validated'), ('DOWNLOAD_REQUEST', 'Download request notification'), ('ACCOUNT_CREATED', 'Account created email notification'), ('SASS_CREATED', 'SASS created email notification')], max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('users', models.ManyToManyField(related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
