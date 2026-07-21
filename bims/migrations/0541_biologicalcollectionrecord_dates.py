from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0540_chemicalrecord_custodian'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='created_date',
            field=models.DateTimeField(
                blank=True,
                help_text='When this record was first created locally.',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='modified_date',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text=(
                    'When this record was last modified locally (e.g. '
                    'harvested or edited). Used to prioritise which records to '
                    're-check against upstream sources such as GBIF.'
                ),
                null=True,
            ),
        ),
    ]
