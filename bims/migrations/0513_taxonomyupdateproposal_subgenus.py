from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0512_merge_20260406_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxonomyupdateproposal',
            name='subgenus',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='taxonomy_update_proposal_subgenus',
                to='bims.taxonomy',
            ),
        ),
    ]
