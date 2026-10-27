import csv
import io
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from components.importer import ImportRowError, import_csv
from components.models import (
    Component,
    ComponentCategory,
    CoolerSpec,
    CpuSpec,
    MotherboardSpec,
    RamSpec,
)

CPU_HEADER = (
    "mpn,brand,model,msrp,socket,coreCount,threadCount,baseClockGhz,boostClockGhz,"
    "tdpWatts,maxPowerWatts,hasIntegratedGpu,includedCooler"
)
MOTHERBOARD_HEADER = (
    "mpn,brand,model,msrp,chipset,socket,formFactor,memoryType,memorySlots,"
    "maxMemoryGb,m2Slots,sataSlots,hasWifi,pcieLanes,vrmPhases"
)
COOLER_HEADER = (
    "mpn,brand,model,msrp,coolerType,supportedSockets,tdpRatingWatts,heightMm,"
    "ramClearanceMm,radiatorSizeMm,radiatorThicknessMm,radiatorLengthMm,"
    "radiatorWidthMm,fanCount,fanSizeMm,noiseDbMax,weightG,powerConnector"
)


RAM_HEADER = (
    "mpn,brand,model,msrp,memoryType,formFactor,capacityGb,moduleCount,speedMts,"
    "casLatency,voltage,rank,ecc,registered,heightMm,hasHeatspreader,xmpExpo"
)


def read_rows(header, *rows):
    return csv.DictReader(io.StringIO("\n".join([header, *rows])))


class CpuImportTests(TestCase):
    def test_imports_cpu_and_normalizes_socket(self):
        rows = read_rows(
            CPU_HEADER,
            "CPU-1,AMD,Ryzen 5 7600X,299.00,LGA 1700,6,12,4.7,5.3,105,142,true,false",
        )

        success, errors = import_csv(rows, ComponentCategory.CPU)

        self.assertEqual((success, errors), (1, []))
        spec = CpuSpec.objects.select_related("socket").get()
        self.assertEqual(spec.socket.name, "LGA1700")
        self.assertEqual(spec.max_power_watts, 142)
        self.assertTrue(spec.has_integrated_gpu)
        self.assertEqual(spec.effective_power_watts, 142)
        self.assertEqual(spec.component.category, ComponentCategory.CPU)

    def test_optional_max_power_can_be_blank(self):
        rows = read_rows(
            CPU_HEADER,
            "CPU-2,AMD,Ryzen 5 7600,229.00,AM5,6,12,4.7,5.1,65,,false,true",
        )

        success, errors = import_csv(rows, ComponentCategory.CPU)

        self.assertEqual((success, errors), (1, []))
        spec = CpuSpec.objects.get()
        self.assertIsNone(spec.max_power_watts)
        self.assertEqual(spec.effective_power_watts, 65)
        self.assertTrue(spec.included_cooler)

    def test_bad_numeric_row_is_reported_and_rolled_back(self):
        rows = read_rows(
            CPU_HEADER,
            "CPU-BAD,AMD,Broken,299.00,AM5,6,12,4.7,5.3,abc,142,true,false",
        )

        success, errors = import_csv(rows, ComponentCategory.CPU)

        self.assertEqual(success, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("Row 2", errors[0])
        self.assertIn("tdpWatts", errors[0])
        self.assertFalse(Component.objects.filter(mpn="CPU-BAD").exists())

    def test_one_bad_row_does_not_stop_good_rows(self):
        rows = read_rows(
            CPU_HEADER,
            "CPU-BAD,AMD,Broken,299.00,AM5,6,12,4.7,5.3,abc,142,true,false",
            "CPU-GOOD,AMD,Working,299.00,AM5,6,12,4.7,5.3,105,142,true,false",
        )

        success, errors = import_csv(rows, ComponentCategory.CPU)

        self.assertEqual(success, 1)
        self.assertEqual(len(errors), 1)
        self.assertTrue(Component.objects.filter(mpn="CPU-GOOD").exists())

    def test_missing_required_column_is_reported(self):
        rows = read_rows(
            "mpn,brand,model,msrp",
            "CPU-3,AMD,No Specs,299.00",
        )

        success, errors = import_csv(rows, ComponentCategory.CPU)

        self.assertEqual(success, 0)
        self.assertIn("socket", errors[0])


class MotherboardImportTests(TestCase):
    def test_imports_motherboard_and_normalizes_enums(self):
        rows = read_rows(
            MOTHERBOARD_HEADER,
            "MB-1,MSI,MAG B650,199.00,B650,am5,Micro ATX,ddr5,4,192,3,6,true,"
            "1x PCIe 5.0 x16,16+2+2",
        )

        success, errors = import_csv(rows, ComponentCategory.MOTHERBOARD)

        self.assertEqual((success, errors), (1, []))
        spec = MotherboardSpec.objects.select_related("socket").get()
        self.assertEqual(spec.socket.name, "AM5")
        self.assertEqual(spec.form_factor, "Micro-ATX")
        self.assertEqual(spec.memory_type, "DDR5")
        self.assertTrue(spec.has_wifi)
        self.assertEqual(spec.m2_slots, 3)

    def test_invalid_form_factor_is_rejected(self):
        rows = read_rows(
            MOTHERBOARD_HEADER,
            "MB-2,MSI,Bad Board,199.00,B650,AM5,BTX,DDR5,4,192,3,6,false,, ",
        )

        success, errors = import_csv(rows, ComponentCategory.MOTHERBOARD)

        self.assertEqual(success, 0)
        self.assertIn("formFactor", errors[0])


class CoolerImportTests(TestCase):
    def test_imports_air_cooler_with_multiple_sockets(self):
        rows = read_rows(
            COOLER_HEADER,
            'COOL-1,Noctua,NH-D15,109.95,Air,"AM4, AM5, LGA 1700",250,165,32,,,,,2,140,24.6,1320,4-pin PWM',
        )

        success, errors = import_csv(rows, ComponentCategory.COOLER)

        self.assertEqual((success, errors), (1, []))
        spec = CoolerSpec.objects.get()
        self.assertEqual(spec.cooler_type, "Air")
        self.assertEqual(spec.tdp_rating_watts, 250)
        self.assertEqual(spec.height_mm, 165)
        self.assertEqual(spec.ram_clearance_mm, 32)
        self.assertEqual(spec.fan_count, 2)
        self.assertEqual(spec.noise_db_max, 24.6)
        self.assertEqual(
            sorted(spec.supported_sockets.values_list("name", flat=True)),
            ["AM4", "AM5", "LGA1700"],
        )
        self.assertEqual(spec.component.category, ComponentCategory.COOLER)

    def test_imports_aio_cooler(self):
        rows = read_rows(
            COOLER_HEADER,
            "AIO-1,Arctic,Liquid Freezer III 360,129.99,aio,AM5;LGA1700,300,,,360,30,398,120,3,120,22.5,1810,SATA",
        )

        success, errors = import_csv(rows, ComponentCategory.COOLER)

        self.assertEqual((success, errors), (1, []))
        spec = CoolerSpec.objects.get()
        self.assertEqual(spec.cooler_type, "AIO")
        self.assertIsNone(spec.height_mm)
        self.assertEqual(spec.radiator_size_mm, 360)
        self.assertEqual(spec.radiator_thickness_mm, 30)
        self.assertEqual(spec.power_connector, "SATA")

    def test_accepts_decimal_dimensions(self):
        rows = read_rows(
            COOLER_HEADER,
            'COOL-DECIMAL,Brand,Tower,79.99,Air,"AM5",180,159.4,32.5,,,,,1,120,22.0,900,4-pin',
        )

        success, errors = import_csv(rows, ComponentCategory.COOLER)

        self.assertEqual((success, errors), (1, []))
        spec = CoolerSpec.objects.get()
        self.assertEqual(spec.height_mm, 159.4)
        self.assertEqual(spec.ram_clearance_mm, 32.5)

    def test_cooler_requires_at_least_one_socket(self):
        rows = read_rows(
            COOLER_HEADER,
            "COOL-2,Brand,Cooler,50.00,Air,,150,120,,,,,,,,,,",
        )

        success, errors = import_csv(rows, ComponentCategory.COOLER)

        self.assertEqual(success, 0)
        self.assertIn("supportedSockets", errors[0])

    def test_mpn_cannot_be_reused_across_categories(self):
        rows = read_rows(
            CPU_HEADER,
            "SHARED-1,AMD,CPU,299.00,AM5,6,12,4.7,5.3,105,142,true,false",
        )
        import_csv(rows, ComponentCategory.CPU)

        rows = read_rows(
            COOLER_HEADER,
            'SHARED-1,Brand,Cooler,50.00,Air,"AM5",150,120,,,,,,1,120,20,500,4-pin',
        )
        success, errors = import_csv(rows, ComponentCategory.COOLER)

        self.assertEqual(success, 0)
        self.assertIn("already exists as CPU", errors[0])
        self.assertEqual(CoolerSpec.objects.count(), 0)


class ImportCategoryTests(TestCase):
    def test_unknown_category_raises(self):
        with self.assertRaises(ImportRowError):
            import_csv(read_rows(CPU_HEADER), "GPU")

    def test_shipped_cooler_template_is_valid(self):
        path = Path(settings.BASE_DIR) / "sample_data" / "coolers_template.csv"
        with path.open(encoding="utf-8", newline="") as csv_file:
            success, errors = import_csv(
                csv.DictReader(csv_file), ComponentCategory.COOLER
            )

        self.assertEqual((success, errors), (2, []))
        self.assertEqual(CoolerSpec.objects.count(), 2)


class RamImportTests(TestCase):
    def test_imports_ram_kit_with_defaults(self):
        rows = read_rows(
            RAM_HEADER,
            "RAM-1,Corsair,Vengeance,89.99,DDR5,DIMM,16,2,6000,30,1.35,Single,"
            "false,false,35,true,EXPO",
        )

        success, errors = import_csv(rows, ComponentCategory.RAM)

        self.assertEqual((success, errors), (1, []))
        spec = RamSpec.objects.get()
        self.assertEqual(spec.memory_type, "DDR5")
        self.assertEqual(spec.form_factor, "DIMM")
        self.assertEqual(spec.total_capacity_gb, 32)
        self.assertEqual(spec.first_word_latency_ns, 10.0)
        self.assertEqual(spec.rank, "Single")

    def test_defaults_to_one_module_and_dimm(self):
        rows = read_rows(
            RAM_HEADER,
            "RAM-2,Crucial,Basic,39.99,DDR5,,16,,4800,,,,,,,,false",
        )

        success, errors = import_csv(rows, ComponentCategory.RAM)

        self.assertEqual((success, errors), (1, []))
        spec = RamSpec.objects.get()
        self.assertEqual(spec.module_count, 1)
        self.assertEqual(spec.form_factor, "DIMM")
        self.assertEqual(spec.rank, "")
        self.assertFalse(spec.has_heatspreader)

    def test_normalizes_so_dimm_and_rank_aliases(self):
        rows = read_rows(
            RAM_HEADER,
            "RAM-3,Kingston,Impact,49.99,DDR5,so-dimm,16,2,5600,46,1.1,2R,"
            "false,false,30,false,None",
        )

        success, errors = import_csv(rows, ComponentCategory.RAM)

        self.assertEqual((success, errors), (1, []))
        spec = RamSpec.objects.get()
        self.assertEqual(spec.form_factor, "SO-DIMM")
        self.assertEqual(spec.rank, "Dual")

    def test_rejects_invalid_memory_type(self):
        rows = read_rows(
            RAM_HEADER,
            "RAM-4,Brand,Model,49.99,DDR3,DIMM,8,2,1600,11,1.5,,false,false,"
            "31,false,",
        )

        success, errors = import_csv(rows, ComponentCategory.RAM)

        self.assertEqual(success, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("memoryType", errors[0])

    def test_registered_memory_requires_ecc(self):
        rows = read_rows(
            RAM_HEADER,
            "RAM-5,Samsung,Server,199.99,DDR5,DIMM,32,1,4800,40,1.1,Dual,"
            "false,true,31,false,",
        )

        success, errors = import_csv(rows, ComponentCategory.RAM)

        self.assertEqual(success, 0)
        self.assertIn("registered", errors[0])

    def test_rejects_zero_capacity_or_speed(self):
        for field, row in (
            ("capacityGb", "RAM-6,Brand,Model,49.99,DDR5,DIMM,0,2,6000,30,1.1,,false,false,35,false,"),
            ("speedMts", "RAM-7,Brand,Model,49.99,DDR5,DIMM,16,2,0,30,1.1,,false,false,35,false,"),
        ):
            with self.subTest(field=field):
                success, errors = import_csv(read_rows(RAM_HEADER, row), ComponentCategory.RAM)
                self.assertEqual(success, 0)
                self.assertIn(field, errors[0])
