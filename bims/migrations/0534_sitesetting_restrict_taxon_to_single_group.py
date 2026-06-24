from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0533_checklistsnapshot_accepted_taxon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='restrict_taxon_to_single_group',
            field=models.BooleanField(
                default=True,
                help_text=(
                    'When enabled, a taxon that already belongs to a taxon group '
                    'cannot be added to a different group.'
                ),
            ),
        ),
    ]
