from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0538_checklistversioncontributor'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='gbif_harvest_exclusion_rules',
            field=models.JSONField(
                blank=True,
                null=True,
                default=list,
                help_text=(
                    "JSON list of rules applied during GBIF harvesting. Each rule is an "
                    "object with 'field' (DwC field name), 'condition' (not_empty | equals "
                    "| contains | greater_than | less_than), optional 'value', and optional "
                    "'description'. A record matching ANY rule is skipped."
                ),
            ),
        ),
    ]
