# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0537_taxon_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistVersionContributor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organisation', models.CharField(blank=True, default='', help_text='Organisation name (editable; used for org-only entries too).', max_length=255)),
                ('note', models.TextField(blank=True, default='', help_text='Contribution role or free-text note (e.g. "Data curation").')),
                ('order', models.PositiveIntegerField(default=0)),
                ('checklist_version', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='version_contributors',
                    to='bims.checklistversion',
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    help_text='Linked user account (null for organisation-only entries).',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='checklist_contributions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Checklist Version Contributor',
                'verbose_name_plural': 'Checklist Version Contributors',
                'ordering': ['order', 'id'],
            },
        ),
    ]
