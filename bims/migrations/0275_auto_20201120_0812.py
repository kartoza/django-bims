# Generated by Django 2.2.12 on 2020-11-20 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0274_sitesetting_enable_remove_all_occurrences_tool'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='landing_page_occurrence_records_title',
            field=models.CharField(default='BIODIVERSITY OCCURRENCE RECORDS', help_text='Header title for Biodiversity Occurrence Records section in landing page', max_length=150),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='landing_page_partners_title',
            field=models.CharField(default='PARTNERS', help_text='Header title for Partners section in landing page', max_length=150),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='recaptcha_secret_key',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='recaptcha_site_key',
            field=models.CharField(default='', max_length=150),
        ),
    ]
