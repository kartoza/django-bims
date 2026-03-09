# Generated migration for data_licence field on UploadRequest

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0497_taxonomy_created_at_taxonomy_last_modified_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadrequest',
            name='data_licence',
            field=models.CharField(
                choices=[
                    ('CC0', 'CC0 1.0 – Public Domain Dedication'),
                    ('CC-BY', 'CC BY 4.0 – Attribution'),
                    ('CC-BY-NC', 'CC BY-NC 4.0 – Attribution-NonCommercial'),
                ],
                default='CC-BY',
                help_text='Creative Commons licence that applies to this dataset',
                max_length=20,
            ),
        ),
    ]
