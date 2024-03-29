# Generated by Django 2.2.12 on 2020-08-11 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0252_auto_20200810_0302'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='blog_page_link',
            field=models.CharField(blank=True, help_text='Link to blog page', max_length=100),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='docs_page_link',
            field=models.CharField(blank=True, help_text='Link to docs page', max_length=100),
        ),
    ]
