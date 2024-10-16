# Generated by Django 4.2.11 on 2024-07-10 15:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0424_taxonomyupdateproposal_taxon_group_under_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxonomyupdateproposal',
            name='accepted_taxonomy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taxonomy_update_proposal_accepted_taxonomy', to='bims.taxonomy'),
        ),
        migrations.AlterField(
            model_name='taxonomyupdateproposal',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_parent', to='bims.taxonomy', verbose_name='Parent'),
        ),
    ]
