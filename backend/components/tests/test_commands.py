import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from components.models import (
    Component,
    ComponentCategory,
    Cooler,
    Cpu,
    Motherboard,
    Ram,
)
from components.tests.factories import make_cooler, make_cpu, make_motherboard, make_ram


class DataPortabilityCommandTests(TestCase):
    def setUp(self):
        self.cpu = make_cpu(
            mpn="CPU-PORT-1", socket_name="AM5", max_power_watts=142, tdp_watts=105
        )
        self.motherboard = make_motherboard(
            mpn="MB-PORT-1", socket_name="AM5", form_factor="Micro-ATX"
        )
        self.cooler = make_cooler(
            mpn="COOL-PORT-1",
            socket_names=("AM4", "AM5", "LGA1700"),
            radiator_size_mm=360,
            height_mm=None,
            cooler_type="AIO",
        )
        self.ram = make_ram(
            mpn="RAM-PORT-1",
            memory_type="DDR4",
            capacity_gb=32,
            module_count=2,
            speed_mts=3600,
            cas_latency=18,
            height_mm=44,
            has_heatspreader=True,
            xmp_expo="XMP 2.0",
        )
        # A component without a spec must not break the export.
        Component.objects.create(
            mpn="MB-BROKEN-1",
            brand="Test",
            model="No Spec Board",
            msrp="100.00",
            category=ComponentCategory.MOTHERBOARD,
        )

    def test_export_then_import_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = StringIO()
            call_command("export_components", output=tmp, stdout=stdout)
            self.assertIn("Skipping 1 Motherboard", stdout.getvalue())

            Component.objects.all().delete()

            errors = StringIO()
            call_command("import_components", tmp, all=True, stdout=StringIO(), stderr=errors)

        self.assertEqual(errors.getvalue(), "")
        self.assertEqual(Cpu.objects.count(), 1)
        self.assertEqual(Motherboard.objects.count(), 1)  # broken row was skipped
        self.assertEqual(Cooler.objects.count(), 1)
        self.assertEqual(Ram.objects.count(), 1)

        cpu = Cpu.objects.select_related("cpu_spec__socket").get()
        self.assertEqual(cpu.cpu_spec.socket.name, "AM5")
        self.assertEqual(cpu.cpu_spec.max_power_watts, 142)
        self.assertEqual(cpu.cpu_spec.effective_power_watts, 142)

        board = Motherboard.objects.select_related("motherboard_spec").get()
        self.assertEqual(board.motherboard_spec.form_factor, "Micro-ATX")

        cooler = Cooler.objects.select_related("cooler_spec").get()
        self.assertEqual(cooler.cooler_spec.cooler_type, "AIO")
        self.assertEqual(cooler.cooler_spec.radiator_size_mm, 360)
        self.assertIsNone(cooler.cooler_spec.height_mm)
        self.assertEqual(
            sorted(cooler.cooler_spec.supported_sockets.values_list("name", flat=True)),
            ["AM4", "AM5", "LGA1700"],
        )

        ram = Ram.objects.select_related("ram_spec").get()
        self.assertEqual(ram.ram_spec.memory_type, "DDR4")
        self.assertEqual(ram.ram_spec.total_capacity_gb, 64)
        self.assertEqual(ram.ram_spec.first_word_latency_ns, 10.0)
        self.assertEqual(ram.ram_spec.height_mm, 44)
        self.assertTrue(ram.ram_spec.has_heatspreader)
        self.assertEqual(ram.ram_spec.xmp_expo, "XMP 2.0")
