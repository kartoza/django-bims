from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0551_delete_climatedata_gbifpublishconfigproxy_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='start_embargo_date',
            field=models.DateField(blank=True, help_text='The date when the embargo on the data starts. Together with the end embargo date, the data is only visible to its owner between these dates.', null=True),
        ),
    ]
