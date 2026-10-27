# Step 2 of the socket normalisation.
#
# This migration contains schema changes only. The data was copied into
# socket_ref by 0005, so the old CharFields can now be removed and the new
# foreign keys renamed into place.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0006_populate_sockets'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cpuspec',
            name='socket',
        ),
        migrations.RemoveField(
            model_name='motherboardspec',
            name='socket',
        ),
        migrations.RenameField(
            model_name='cpuspec',
            old_name='socket_ref',
            new_name='socket',
        ),
        migrations.RenameField(
            model_name='motherboardspec',
            old_name='socket_ref',
            new_name='socket',
        ),
        migrations.AlterField(
            model_name='cpuspec',
            name='socket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cpu_specs', to='components.socket'),
        ),
        migrations.AlterField(
            model_name='motherboardspec',
            name='socket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='motherboard_specs', to='components.socket'),
        ),
    ]
