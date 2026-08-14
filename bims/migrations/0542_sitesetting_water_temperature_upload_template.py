from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0541_biologicalcollectionrecord_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='water_temperature_upload_template',
            field=models.FileField(
                blank=True,
                help_text='File template for water temperature uploader',
                null=True,
                upload_to='',
            ),
        ),
    ]
