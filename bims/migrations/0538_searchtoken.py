import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0537_taxon_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchToken',
            fields=[
                ('token', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('schema_name', models.CharField(max_length=63)),
                ('site_ids', django.contrib.postgres.fields.ArrayField(
                    base_field=models.IntegerField(),
                    default=list,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
            ],
            options={
                'indexes': [
                    models.Index(
                        fields=['expires_at'],
                        name='bims_searchtoken_expires_idx',
                    ),
                ],
            },
        ),
    ]
