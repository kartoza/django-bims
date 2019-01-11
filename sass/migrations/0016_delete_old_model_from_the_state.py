from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0015_update_relations'),
    ]

    state_operations = [
        migrations.DeleteModel('SassBiotope'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
