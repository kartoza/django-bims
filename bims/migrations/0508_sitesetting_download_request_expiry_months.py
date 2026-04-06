from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0507_gbifpublishcontact_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='download_request_expiry_months',
            field=models.PositiveSmallIntegerField(
                default=2,
                null=True,
                blank=True,
                help_text=(
                    'Number of months to keep approved download files before they '
                    'are automatically deleted. Leave blank or set to 0 for files '
                    'to never expire.'
                ),
            ),
        ),
    ]
