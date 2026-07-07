import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0536_biologicalcollectionrecord_doi'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonURL',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.URLField(max_length=2000)),
                ('label', models.CharField(max_length=255)),
                ('taxonomy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='urls', to='bims.taxonomy')),
            ],
            options={
                'verbose_name': 'Taxon URL',
                'verbose_name_plural': 'Taxon URLs',
                'ordering': ['label'],
            },
        ),
    ]
