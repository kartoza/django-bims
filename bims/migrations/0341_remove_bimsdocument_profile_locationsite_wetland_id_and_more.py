# Generated by Django 4.1.10 on 2023-08-15 07:52

from django.conf import settings
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('bims', '0340_auto_20230714_0645'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bimsdocument',
            name='profile',
        ),
        migrations.AddField(
            model_name='locationsite',
            name='wetland_id',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='basemaplayer',
            name='additional_params',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='biologicalcollectionrecord',
            name='additional_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='biologicalcollectionrecord',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='biologicalcollectionrecord',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='biotope',
            name='additional_data',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
        migrations.AlterField(
            model_name='chemicalrecord',
            name='additional_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dashboardconfiguration',
            name='additional_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='locationsite',
            name='additional_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Additional json data'),
        ),
        migrations.AlterField(
            model_name='locationsite',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='locationsite',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='locationsite',
            name='location_context',
            field=models.JSONField(blank=True, help_text='This is intended for filtering', null=True, verbose_name='Formatted location_context_document'),
        ),
        migrations.AlterField(
            model_name='locationsite',
            name='location_context_document',
            field=models.JSONField(blank=True, help_text='This document is generated from GeoContext by using management command or changing the geometry.', null=True, verbose_name='Document for location context as JSON.'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='data',
            field=models.JSONField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='sitesetting',
            name='map_default_filters',
            field=models.JSONField(default=[], help_text='Which filters are selected by default, the format must be as follows : [{"filter_key": "sourceCollection", "filter_values": ["bims"]}]'),
        ),
        migrations.AlterField(
            model_name='sourcereference',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='survey',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='survey',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='additional_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Additional json data'),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='analyst',
            field=models.ForeignKey(blank=True, help_text='The person that did the analysis', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_analyst', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='collector_user',
            field=models.ForeignKey(blank=True, help_text='The user object of the actual capturer/collector of this data', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_collector_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='gbif_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Json data from gbif'),
        ),
        migrations.AlterField(
            model_name='taxonomy',
            name='rank',
            field=models.CharField(blank=True, choices=[('SUBSPECIES', 'Sub Species'), ('SPECIES', 'Species'), ('GENUS', 'Genus'), ('FAMILY', 'Family'), ('SUPERFAMILY', 'Super Family'), ('ORDER', 'Order'), ('CLASS', 'Class'), ('SUBCLASS', 'Sub Class'), ('PHYLUM', 'Phylum'), ('SUBPHYLUM', 'SubPhylum'), ('KINGDOM', 'Kingdom'), ('DOMAIN', 'Domain'), ('LIFE', 'Life'), ('CULTIVAR_GROUP', 'Cultivar Group'), ('SUBORDER', 'Sub Order'), ('INFRAORDER', 'Infra Order'), ('SUBFAMILY', 'Sub Family'), ('VARIETY', 'Variety')], max_length=50, verbose_name='Taxonomic Rank'),
        ),
    ]
