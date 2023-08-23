# Generated by Django 4.1.10 on 2023-08-15 07:52

from django.conf import settings
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sass', '0058_auto_20220126_0853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='river',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='river',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sasstaxon',
            name='additional_data',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='additional_data',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='collector',
            field=models.ForeignKey(blank=True, help_text='Actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_data_collector', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='owner',
            field=models.ForeignKey(blank=True, help_text='Creator/owner of this data from the web', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_owner', to=settings.AUTH_USER_MODEL),
        ),
    ]