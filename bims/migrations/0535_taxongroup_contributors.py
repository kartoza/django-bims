from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0534_sitesetting_restrict_taxon_to_single_group'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='taxongroup',
            name='contributors',
            field=models.ManyToManyField(
                blank=True,
                related_name='contributor_taxon_groups',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
