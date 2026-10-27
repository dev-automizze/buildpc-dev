# Step 1 of the socket normalisation: schema only.
#
# The existing socket columns are left untouched. New nullable socket_ref
# foreign keys are added; 0006 copies the old strings into them.
#
# Schema changes and data writes are intentionally split across migrations
# because PostgreSQL rejects deferred CREATE INDEX statements after a table has
# pending trigger events in the same transaction.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0004_motherboardspec_pcie_lanes_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Socket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Cooler',
            fields=[
            ],
            options={
                'verbose_name': 'Cooler',
                'verbose_name_plural': 'Coolers',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('components.component',),
        ),
        migrations.AddField(
            model_name='cpuspec',
            name='max_power_watts',
            field=models.PositiveIntegerField(blank=True, help_text='Sustained package power (AMD PPT / Intel PL2). Falls back to TDP when empty.', null=True),
        ),
        migrations.AlterField(
            model_name='component',
            name='category',
            field=models.CharField(choices=[('CPU', 'CPU'), ('Motherboard', 'Motherboard'), ('Cooler', 'Cooler')], db_index=True, default='CPU', max_length=50),
        ),
        migrations.AlterField(
            model_name='motherboardspec',
            name='form_factor',
            field=models.CharField(choices=[('ATX', 'ATX'), ('Micro-ATX', 'Micro-ATX'), ('Mini-ITX', 'Mini-ITX'), ('E-ATX', 'E-ATX'), ('EEB', 'EEB'), ('Deep Micro-ATX', 'Deep Micro-ATX')], help_text='e.g., ATX, Micro-ATX, Mini-ITX', max_length=20),
        ),
        migrations.AlterField(
            model_name='motherboardspec',
            name='memory_type',
            field=models.CharField(choices=[('DDR4', 'DDR4'), ('DDR5', 'DDR5')], help_text='e.g., DDR4, DDR5', max_length=10),
        ),
        migrations.CreateModel(
            name='CoolerSpec',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cooler_type', models.CharField(choices=[('Air', 'Air'), ('AIO', 'AIO Liquid'), ('Passive', 'Passive')], default='Air', max_length=20)),
                ('tdp_rating_watts', models.PositiveIntegerField(help_text='Manufacturer rated heat dissipation in watts.')),
                ('height_mm', models.PositiveIntegerField(blank=True, help_text='Air cooler height in mm. Leave empty for liquid coolers.', null=True)),
                ('ram_clearance_mm', models.PositiveIntegerField(blank=True, help_text='Clearance under the heatsink for memory modules, in mm.', null=True)),
                ('radiator_size_mm', models.PositiveIntegerField(blank=True, help_text='Radiator size in mm, e.g. 240, 280, 360. Leave empty for air coolers.', null=True)),
                ('radiator_thickness_mm', models.PositiveIntegerField(blank=True, null=True)),
                ('radiator_length_mm', models.PositiveIntegerField(blank=True, null=True)),
                ('radiator_width_mm', models.PositiveIntegerField(blank=True, null=True)),
                ('fan_count', models.PositiveIntegerField(default=1)),
                ('fan_size_mm', models.PositiveIntegerField(blank=True, null=True)),
                ('noise_db_max', models.FloatField(blank=True, help_text='Maximum noise level in dBA.', null=True)),
                ('weight_g', models.PositiveIntegerField(blank=True, null=True)),
                ('power_connector', models.CharField(blank=True, default='', help_text='e.g., 4-pin PWM, SATA power, Molex', max_length=50)),
                ('component', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cooler_spec', to='components.component')),
                ('supported_sockets', models.ManyToManyField(related_name='cooler_specs', to='components.socket')),
            ],
        ),
        migrations.AddField(
            model_name='cpuspec',
            name='socket_ref',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cpu_specs', to='components.socket'),
        ),
        migrations.AddField(
            model_name='motherboardspec',
            name='socket_ref',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='motherboard_specs', to='components.socket'),
        ),
    ]
