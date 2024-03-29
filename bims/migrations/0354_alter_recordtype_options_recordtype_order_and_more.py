# Generated by Django 4.1.10 on 2023-10-04 02:29

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bims', '0353_rename_record_type_link_biologicalcollectionrecord_record_type_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recordtype',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='recordtype',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='order'),
            preserve_default=False,
        ),
    ]
