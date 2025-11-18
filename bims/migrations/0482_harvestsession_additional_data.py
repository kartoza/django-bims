# Generated manually for harvest resume functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0481_alter_taxonomy_scientific_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='harvestsession',
            name='additional_data',
            field=models.JSONField(blank=True, help_text='JSON field for storing resume state and other metadata', null=True),
        ),
    ]
