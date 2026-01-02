from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0487_populate_data_sources'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilterPanelInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Matches the filter heading, e.g. "SPATIAL" or "TEMPORAL".', max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Filter panel description',
                'verbose_name_plural': 'Filter panel descriptions',
                'ordering': ('title',),
            },
        ),
    ]
