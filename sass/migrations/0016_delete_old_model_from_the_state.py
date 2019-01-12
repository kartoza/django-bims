from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0015_update_relations'),
        ('bims', '0104_auto_20190111_0928')
    ]

    state_operations = [
        migrations.DeleteModel('SassBiotope'),
        migrations.AlterField(
            model_name='sassbiotopefraction',
            name='sass_biotope',
            field=models.ForeignKey(
                'bims.biotope',
                on_delete=models.CASCADE,
                default=None,
                null=True,
                blank=True
            )
        )
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
