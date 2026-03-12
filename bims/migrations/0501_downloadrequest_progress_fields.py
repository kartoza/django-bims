from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0500_sitesetting_allow_public_taxa_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='downloadrequest',
            name='progress_updated_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp of the last progress update'
            ),
        ),
        migrations.AddField(
            model_name='downloadrequest',
            name='download_path',
            field=models.CharField(
                blank=True,
                max_length=512,
                null=True,
                help_text='Filesystem path of the in-progress download file'
            ),
        ),
        migrations.AddField(
            model_name='downloadrequest',
            name='download_params',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='Serialised request parameters used to start the download'
            ),
        ),
    ]
