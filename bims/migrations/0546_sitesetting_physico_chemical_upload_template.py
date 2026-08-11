from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0545_fix_national_conservation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='physico_chemical_upload_template',
            field=models.FileField(
                blank=True,
                help_text='File template for physico-chemical data uploader',
                null=True,
                upload_to='',
            ),
        ),
    ]
