from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0498_uploadrequest_data_licence'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadsession',
            name='last_progress_update',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp of the last progress update, used to detect stale/stuck tasks'
            ),
        ),
        migrations.AddField(
            model_name='uploadsession',
            name='start_row',
            field=models.IntegerField(
                default=0,
                help_text='Row index to resume processing from (0 = start from beginning)'
            ),
        ),
    ]
