from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0499_uploadsession_auto_resume'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='allow_public_taxa_view',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Allow non-logged-in users to view the taxa management page. '
                    'Public users will only see validated taxa. '
                    'Downloading still requires login.'
                )
            ),
        ),
    ]
