from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0488_filterpanelinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='show_general_summary_on_landing',
            field=models.BooleanField(
                default=False,
                help_text='Display the general statistics block on the landing page.'
            ),
        ),
    ]
