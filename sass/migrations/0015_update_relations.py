from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0014_auto_20190111_0809'),
        ('bims', '0103_move_sass_biotope_model'),
    ]

    state_operations = [
        migrations.AlterField(
            model_name='sassbiotopefraction',
            name='sass_biotope',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='bims.SassBiotope'),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]