from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0489_sitesetting_show_general_summary'),
    ]

    operations = [
        migrations.CreateModel(
            name='IUCNAssessment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_id', models.BigIntegerField()),
                ('sis_taxon_id', models.IntegerField(blank=True, null=True)),
                ('year_published', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('latest', models.BooleanField(default=False)),
                ('possibly_extinct', models.BooleanField(default=False)),
                ('possibly_extinct_in_the_wild', models.BooleanField(default=False)),
                ('red_list_category_code', models.CharField(blank=True, default='', max_length=20)),
                ('url', models.URLField(blank=True, default='', max_length=255)),
                ('scope_code', models.CharField(blank=True, default='', max_length=10)),
                ('scope_label', models.CharField(blank=True, default='', max_length=100)),
                ('raw_data', models.JSONField(blank=True, null=True)),
                ('normalized_status', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assessments',
                    to='bims.iucnstatus'
                )),
                ('taxonomy', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='iucn_assessments',
                    to='bims.taxonomy'
                )),
            ],
            options={
                'verbose_name': 'IUCN Assessment',
                'verbose_name_plural': 'IUCN Assessments',
                'ordering': ['-year_published', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='iucnassessment',
            index=models.Index(fields=['taxonomy', 'year_published'], name='bims_iucna_taxono_e8bb7c_idx'),
        ),
        migrations.AddIndex(
            model_name='iucnassessment',
            index=models.Index(fields=['taxonomy', 'latest'], name='bims_iucna_taxono_9626f4_idx'),
        ),
        migrations.AddConstraint(
            model_name='iucnassessment',
            constraint=models.UniqueConstraint(
                fields=['taxonomy', 'assessment_id'],
                name='uniq_iucn_assessment_taxonomy_assessment_id',
            ),
        ),
    ]
