# Generated by Django 2.2.16 on 2022-01-26 08:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0057_auto_20200619_0618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitevisitbiotopetaxon',
            name='biotope',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bims.Biotope'),
        ),
    ]
