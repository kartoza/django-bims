from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0538_searchtoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpenSearchReindexRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('recreate', models.BooleanField(default=False)),
                ('chunk_size', models.PositiveIntegerField(default=500)),
                ('requested_schema', models.CharField(blank=True, default='', max_length=63)),
                ('total_tenants', models.PositiveIntegerField(default=0)),
                ('completed_tenants', models.PositiveIntegerField(default=0)),
                ('failed_tenants', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True, default='')),
            ],
            options={
                'ordering': ('-started_at', '-id'),
            },
        ),
        migrations.CreateModel(
            name='OpenSearchReindexTenantStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema_name', models.CharField(max_length=63)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('records_indexed', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True, default='')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_statuses', to='bims.opensearchreindexrun')),
            ],
            options={
                'ordering': ('schema_name',),
                'unique_together': {('run', 'schema_name')},
            },
        ),
    ]
