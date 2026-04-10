import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0514_biologicalcollectionrecord_coordinate_precision_and_more'),
        ('td_biblio', '0008_alter_entry_crossref'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # The M2M table already exists; just add the order column.
                migrations.RunSQL(
                    sql="ALTER TABLE bims_sourcereference_source_authors ADD COLUMN IF NOT EXISTS \"order\" integer NOT NULL DEFAULT 0;",
                    reverse_sql="ALTER TABLE bims_sourcereference_source_authors DROP COLUMN IF EXISTS \"order\";",
                ),
            ],
            state_operations=[
                # Register the through model in Django's state, pointing at the
                # existing auto-created M2M table so no new table is created.
                migrations.CreateModel(
                    name='SourceReferenceAuthor',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('order', models.PositiveIntegerField(default=0)),
                        ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_reference_authorships', to='td_biblio.author')),
                        ('source_reference', models.ForeignKey(db_column='sourcereference_id', on_delete=django.db.models.deletion.CASCADE, related_name='source_reference_authors', to='bims.sourcereference')),
                    ],
                    options={
                        'ordering': ['order'],
                        'unique_together': {('source_reference', 'author')},
                        'db_table': 'bims_sourcereference_source_authors',
                    },
                ),
                # Tell Django the M2M field now uses the through model (state only).
                migrations.AlterField(
                    model_name='sourcereference',
                    name='source_authors',
                    field=models.ManyToManyField(
                        blank=True,
                        help_text='Author(s) of this source reference',
                        related_name='source_references',
                        through='bims.SourceReferenceAuthor',
                        to='td_biblio.author',
                    ),
                ),
            ],
        ),
    ]
