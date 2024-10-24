# Generated by Django 4.2.8 on 2024-02-29 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0390_merge_20240228_1048'),
    ]

    operations = [
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='accuracy_of_identification',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of identification (0-100).'),
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='accuracy_of_locality',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of locality information (0-100).'),
        ),
        migrations.AddField(
            model_name='biologicalcollectionrecord',
            name='reliability_of_sources',
            field=models.IntegerField(default=0, help_text='Score for the reliability of the sources (0-100).'),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='accuracy_of_identification',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of identification (0-100).'),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='accuracy_of_locality',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of locality information (0-100).'),
        ),
        migrations.AddField(
            model_name='locationsite',
            name='reliability_of_sources',
            field=models.IntegerField(default=0, help_text='Score for the reliability of the sources (0-100).'),
        ),
        migrations.AddField(
            model_name='survey',
            name='accuracy_of_identification',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of identification (0-100).'),
        ),
        migrations.AddField(
            model_name='survey',
            name='accuracy_of_locality',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of locality information (0-100).'),
        ),
        migrations.AddField(
            model_name='survey',
            name='reliability_of_sources',
            field=models.IntegerField(default=0, help_text='Score for the reliability of the sources (0-100).'),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='accuracy_of_identification',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of identification (0-100).'),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='accuracy_of_locality',
            field=models.IntegerField(default=0, help_text='Score for the accuracy of locality information (0-100).'),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='reliability_of_sources',
            field=models.IntegerField(default=0, help_text='Score for the reliability of the sources (0-100).'),
        ),
        migrations.AlterField(
            model_name='downloadrequest',
            name='resource_type',
            field=models.CharField(choices=[('CSV', 'Csv'), ('XLS', 'Xls'), ('CHART', 'Chart'), ('TABLE', 'Table'), ('IMAGE', 'Image')], default='CSV', max_length=10),
        ),
    ]
