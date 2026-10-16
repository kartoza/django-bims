from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0551_delete_climatedata_gbifpublishconfigproxy_and_more'),
    ]

    operations = [
        # The column already exists on some deployments (added out of band),
        # so only add it when missing.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE bims_biologicalcollectionrecord '
                        'ADD COLUMN IF NOT EXISTS start_embargo_date date NULL',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='biologicalcollectionrecord',
                    name='start_embargo_date',
                    field=models.DateField(blank=True, help_text='The date when the embargo on the data starts. Together with the end embargo date, the data is only visible to its owner between these dates.', null=True),
                ),
            ],
        ),
    ]
