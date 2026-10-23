from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0556_ogclayer_cost_control'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='metadata_upload_template',
            field=models.FileField(
                blank=True,
                help_text='File template for dataset metadata, offered to data providers in the upload portal',
                null=True,
                upload_to=''),
        ),
    ]
