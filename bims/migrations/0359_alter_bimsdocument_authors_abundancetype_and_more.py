# Generated by Django 4.1.10 on 2023-10-05 09:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0358_rename_hydroperiod_link_biologicalcollectionrecord_hydroperiod_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbundanceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('name', models.CharField(max_length=256)),
                ('specific_module', models.ForeignKey(blank=True, help_text='If specified, then this abundance type will be available only for this module.', null=True, on_delete=django.db.models.deletion.CASCADE, to='bims.taxongroup')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='abundance_type_link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.abundancetype'),
        ),
    ]
