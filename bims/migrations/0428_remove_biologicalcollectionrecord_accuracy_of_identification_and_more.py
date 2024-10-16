# Generated by Django 4.2.11 on 2024-07-22 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0427_taxonomy_source_reference_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='biologicalcollectionrecord',
            name='accuracy_of_identification',
        ),
        migrations.RemoveField(
            model_name='biologicalcollectionrecord',
            name='accuracy_of_locality',
        ),
        migrations.RemoveField(
            model_name='locationsite',
            name='accuracy_of_identification',
        ),
        migrations.RemoveField(
            model_name='locationsite',
            name='accuracy_of_locality',
        ),
        migrations.RemoveField(
            model_name='survey',
            name='accuracy_of_identification',
        ),
        migrations.RemoveField(
            model_name='survey',
            name='accuracy_of_locality',
        ),
        migrations.RemoveField(
            model_name='taxonomy',
            name='accuracy_of_identification',
        ),
        migrations.RemoveField(
            model_name='taxonomy',
            name='accuracy_of_locality',
        ),
        migrations.RemoveField(
            model_name='taxonomyupdateproposal',
            name='accuracy_of_identification',
        ),
        migrations.RemoveField(
            model_name='taxonomyupdateproposal',
            name='accuracy_of_locality',
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='accuracy_of_coordinates',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='certainty_of_identification',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='accuracy_of_coordinates',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='certainty_of_identification',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='survey',
            name='accuracy_of_coordinates',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='survey',
            name='certainty_of_identification',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='accuracy_of_coordinates',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='certainty_of_identification',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='taxonomyupdateproposal',
            name='accuracy_of_coordinates',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='taxonomyupdateproposal',
            name='certainty_of_identification',
            field=models.CharField(blank=True, default=''),
        ),
    ]
