from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0506_encrypt_gbifpublishconfig_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='gbifpublishcontact',
            name='role',
            field=models.CharField(
                choices=[
                    ('author', 'Author'),
                    ('contentProvider', 'Content Provider'),
                    ('custodianSteward', 'Custodian Steward'),
                    ('distributor', 'Distributor'),
                    ('editor', 'Editor'),
                    ('metadataProvider', 'Metadata Provider'),
                    ('originator', 'Originator'),
                    ('pointOfContact', 'Point of Contact'),
                    ('principalInvestigator', 'Principal Investigator'),
                    ('processor', 'Processor'),
                    ('publisher', 'Publisher'),
                    ('user', 'User'),
                ],
                default='originator',
                help_text=(
                    'How this person or organisation is related to the resource '
                    '(EML roleType). E.g. originator, author, pointOfContact, publisher.'
                ),
                max_length=32,
            ),
        ),
    ]
