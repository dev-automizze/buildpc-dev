from pathlib import Path

import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from components.models import Cooler, Cpu, Motherboard, Ram

CPU_FIELDS = [
    "mpn", "brand", "model", "msrp", "socket", "coreCount", "threadCount",
    "baseClockGhz", "boostClockGhz", "tdpWatts", "maxPowerWatts",
    "hasIntegratedGpu", "includedCooler",
]

MOTHERBOARD_FIELDS = [
    "mpn", "brand", "model", "msrp", "chipset", "socket", "formFactor",
    "memoryType", "memorySlots", "maxMemoryGb", "m2Slots", "sataSlots",
    "hasWifi", "pcieLanes", "vrmPhases",
]

COOLER_FIELDS = [
    "mpn", "brand", "model", "msrp", "coolerType", "supportedSockets",
    "tdpRatingWatts", "heightMm", "ramClearanceMm", "radiatorSizeMm",
    "radiatorThicknessMm", "radiatorLengthMm", "radiatorWidthMm", "fanCount",
    "fanSizeMm", "noiseDbMax", "weightG", "powerConnector",
]

RAM_FIELDS = [
    "mpn", "brand", "model", "msrp", "memoryType", "formFactor", "capacityGb",
    "moduleCount", "speedMts", "casLatency", "voltage", "rank", "ecc",
    "registered", "heightMm", "hasHeatspreader", "xmpExpo",
]


def _bool(value):
    return "true" if value else "false"


def _value(value):
    return "" if value is None else value


def _write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


class Command(BaseCommand):
    help = "Export all components to CSV files that import_components can read."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(settings.BASE_DIR / "exports"),
            help="Directory to write cpus.csv, motherboards.csv, and coolers.csv into.",
        )

    def handle(self, *args, **options):
        output = Path(options["output"])
        output.mkdir(parents=True, exist_ok=True)

        cpu_qs = Cpu.objects.select_related("cpu_spec__socket")
        motherboard_qs = Motherboard.objects.select_related("motherboard_spec__socket")
        cooler_qs = Cooler.objects.select_related("cooler_spec").prefetch_related(
            "cooler_spec__supported_sockets"
        )
        ram_qs = Ram.objects.select_related("ram_spec")

        missing_specs = {
            "CPU": Cpu.objects.filter(cpu_spec__isnull=True).count(),
            "Motherboard": Motherboard.objects.filter(motherboard_spec__isnull=True).count(),
            "Cooler": Cooler.objects.filter(cooler_spec__isnull=True).count(),
            "RAM": Ram.objects.filter(ram_spec__isnull=True).count(),
        }
        for category, count in missing_specs.items():
            if count:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping {count} {category} component(s) without a spec row."
                    )
                )

        cpus = [
            {
                "mpn": c.mpn,
                "brand": c.brand,
                "model": c.model,
                "msrp": c.msrp,
                "socket": c.cpu_spec.socket.name,
                "coreCount": c.cpu_spec.core_count,
                "threadCount": c.cpu_spec.thread_count,
                "baseClockGhz": c.cpu_spec.base_clock_ghz,
                "boostClockGhz": c.cpu_spec.boost_clock_ghz,
                "tdpWatts": c.cpu_spec.tdp_watts,
                "maxPowerWatts": _value(c.cpu_spec.max_power_watts),
                "hasIntegratedGpu": _bool(c.cpu_spec.has_integrated_gpu),
                "includedCooler": _bool(c.cpu_spec.included_cooler),
            }
            for c in cpu_qs.filter(cpu_spec__isnull=False)
        ]

        motherboards = [
            {
                "mpn": m.mpn,
                "brand": m.brand,
                "model": m.model,
                "msrp": m.msrp,
                "chipset": m.motherboard_spec.chipset,
                "socket": m.motherboard_spec.socket.name,
                "formFactor": m.motherboard_spec.form_factor,
                "memoryType": m.motherboard_spec.memory_type,
                "memorySlots": m.motherboard_spec.memory_slots,
                "maxMemoryGb": m.motherboard_spec.max_memory_gb,
                "m2Slots": m.motherboard_spec.m2_slots,
                "sataSlots": m.motherboard_spec.sata_slots,
                "hasWifi": _bool(m.motherboard_spec.has_wifi),
                "pcieLanes": _value(m.motherboard_spec.pcie_lanes),
                "vrmPhases": _value(m.motherboard_spec.vrm_phases),
            }
            for m in motherboard_qs.filter(motherboard_spec__isnull=False)
        ]

        coolers = [
            {
                "mpn": c.mpn,
                "brand": c.brand,
                "model": c.model,
                "msrp": c.msrp,
                "coolerType": c.cooler_spec.cooler_type,
                "supportedSockets": "|".join(
                    c.cooler_spec.supported_sockets.values_list("name", flat=True)
                ),
                "tdpRatingWatts": c.cooler_spec.tdp_rating_watts,
                "heightMm": _value(c.cooler_spec.height_mm),
                "ramClearanceMm": _value(c.cooler_spec.ram_clearance_mm),
                "radiatorSizeMm": _value(c.cooler_spec.radiator_size_mm),
                "radiatorThicknessMm": _value(c.cooler_spec.radiator_thickness_mm),
                "radiatorLengthMm": _value(c.cooler_spec.radiator_length_mm),
                "radiatorWidthMm": _value(c.cooler_spec.radiator_width_mm),
                "fanCount": c.cooler_spec.fan_count,
                "fanSizeMm": _value(c.cooler_spec.fan_size_mm),
                "noiseDbMax": _value(c.cooler_spec.noise_db_max),
                "weightG": _value(c.cooler_spec.weight_g),
                "powerConnector": c.cooler_spec.power_connector,
            }
            for c in cooler_qs.filter(cooler_spec__isnull=False)
        ]

        ram = [
            {
                "mpn": r.mpn,
                "brand": r.brand,
                "model": r.model,
                "msrp": r.msrp,
                "memoryType": r.ram_spec.memory_type,
                "formFactor": r.ram_spec.form_factor,
                "capacityGb": r.ram_spec.capacity_gb,
                "moduleCount": r.ram_spec.module_count,
                "speedMts": r.ram_spec.speed_mts,
                "casLatency": _value(r.ram_spec.cas_latency),
                "voltage": _value(r.ram_spec.voltage),
                "rank": r.ram_spec.rank,
                "ecc": _bool(r.ram_spec.ecc),
                "registered": _bool(r.ram_spec.registered),
                "heightMm": _value(r.ram_spec.height_mm),
                "hasHeatspreader": _bool(r.ram_spec.has_heatspreader),
                "xmpExpo": r.ram_spec.xmp_expo,
            }
            for r in ram_qs.filter(ram_spec__isnull=False)
        ]

        counts = {
            "cpus.csv": _write(output / "cpus.csv", CPU_FIELDS, cpus),
            "motherboards.csv": _write(
                output / "motherboards.csv", MOTHERBOARD_FIELDS, motherboards
            ),
            "coolers.csv": _write(output / "coolers.csv", COOLER_FIELDS, coolers),
            "ram.csv": _write(output / "ram.csv", RAM_FIELDS, ram),
        }

        for name, count in counts.items():
            self.stdout.write(f"{name}: {count} row(s)")
        self.stdout.write(self.style.SUCCESS(f"Exported to {output}"))
