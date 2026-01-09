# Generated manually for UploadType refactoring

from django.db import migrations, models
import django.db.models.deletion


def populate_upload_types(apps, schema_editor):
    """Create initial UploadType records"""
    UploadType = apps.get_model('bims', 'UploadType')

    types = [
        {'name': 'Occurrence Data', 'code': 'occurrence', 'order': 1},
        {'name': 'Spatial Layer', 'code': 'spatial', 'order': 2},
        {'name': 'Species Checklist or Taxonomic Resource', 'code': 'species-checklist', 'order': 3},
    ]

    for type_data in types:
        UploadType.objects.get_or_create(
            code=type_data['code'],
            defaults={'name': type_data['name'], 'order': type_data['order']}
        )


def migrate_upload_type_data(apps, schema_editor):
    """Migrate existing upload_type string values to ForeignKey"""
    UploadRequest = apps.get_model('bims', 'UploadRequest')
    UploadType = apps.get_model('bims', 'UploadType')

    # Create a mapping of code to UploadType instance
    type_map = {ut.code: ut for ut in UploadType.objects.all()}

    # Update all UploadRequest records
    for request in UploadRequest.objects.all():
        if request.upload_type_old and request.upload_type_old in type_map:
            request.upload_type = type_map[request.upload_type_old]
            request.save(update_fields=['upload_type'])


def reverse_migrate_data(apps, schema_editor):
    """Reverse migration: copy FK back to string field"""
    UploadRequest = apps.get_model('bims', 'UploadRequest')

    for request in UploadRequest.objects.all():
        if request.upload_type:
            request.upload_type_old = request.upload_type.code
            request.save(update_fields=['upload_type_old'])


class Migration(migrations.Migration):

    atomic = False  # Disable atomic transactions to avoid pending trigger events

    dependencies = [
        ('bims', '0490_iucnassessment'),
    ]

    operations = [
        # Step 1: Create UploadType model
        migrations.CreateModel(
            name='UploadType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Display name for the upload type', max_length=255)),
                ('code', models.CharField(help_text='Unique identifier code (e.g., occurrence, spatial, species-checklist)', max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='Optional description', null=True)),
                ('order', models.IntegerField(default=0, help_text='Display order in forms')),
            ],
            options={
                'verbose_name': 'Upload Type',
                'verbose_name_plural': 'Upload Types',
                'ordering': ('order',),
            },
        ),

        # Step 2: Populate UploadType with initial data
        migrations.RunPython(populate_upload_types, migrations.RunPython.noop),

        # Step 3: Rename existing upload_type field to upload_type_old
        migrations.RenameField(
            model_name='uploadrequest',
            old_name='upload_type',
            new_name='upload_type_old',
        ),

        # Step 4: Add new upload_type ForeignKey field (nullable for now)
        migrations.AddField(
            model_name='uploadrequest',
            name='upload_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='Type of upload request',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='upload_requests',
                to='bims.uploadtype'
            ),
        ),

        # Step 5: Migrate data from old field to new field
        migrations.RunPython(migrate_upload_type_data, reverse_migrate_data),

        # Step 6: Make upload_type non-nullable
        migrations.AlterField(
            model_name='uploadrequest',
            name='upload_type',
            field=models.ForeignKey(
                help_text='Type of upload request',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='upload_requests',
                to='bims.uploadtype'
            ),
        ),

        # Step 7: Remove the old upload_type_old field
        migrations.RemoveField(
            model_name='uploadrequest',
            name='upload_type_old',
        ),
    ]
