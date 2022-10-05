# Generated by Django 2.2.28 on 2022-10-05 05:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0324_merge_20220912_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taxonomy_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taxonomy_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='ready_for_validation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='validated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='validation_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
