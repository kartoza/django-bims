# Generated by Django 2.2.16 on 2021-10-25 06:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0295_auto_20211025_0256'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonExtraAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('taxon_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bims.TaxonGroup')),
            ],
        ),
    ]
