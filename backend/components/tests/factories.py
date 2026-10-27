from decimal import Decimal

from components.models import (
    Component,
    ComponentCategory,
    Cooler,
    CoolerType,
    CoolerSpec,
    Cpu,
    CpuSpec,
    Motherboard,
    MotherboardSpec,
    Ram,
    RamSpec,
    Socket,
)


def make_socket(name):
    return Socket.objects.get_or_create(name=name)[0]


def make_cpu(mpn="CPU-TEST-1", socket_name="AM5", **overrides):
    component = Component.objects.create(
        mpn=mpn,
        brand=overrides.pop("brand", "AMD"),
        model=overrides.pop("model", "Ryzen Test"),
        msrp=overrides.pop("msrp", Decimal("299.00")),
        category=ComponentCategory.CPU,
    )
    CpuSpec.objects.create(
        component=component,
        socket=make_socket(socket_name),
        core_count=overrides.pop("core_count", 6),
        thread_count=overrides.pop("thread_count", 12),
        base_clock_ghz=overrides.pop("base_clock_ghz", 4.7),
        boost_clock_ghz=overrides.pop("boost_clock_ghz", 5.3),
        tdp_watts=overrides.pop("tdp_watts", 105),
        **overrides,
    )
    return component


def make_motherboard(mpn="MB-TEST-1", socket_name="AM5", **overrides):
    component = Component.objects.create(
        mpn=mpn,
        brand=overrides.pop("brand", "MSI"),
        model=overrides.pop("model", "Test Board"),
        msrp=overrides.pop("msrp", Decimal("199.00")),
        category=ComponentCategory.MOTHERBOARD,
    )
    MotherboardSpec.objects.create(
        component=component,
        socket=make_socket(socket_name),
        chipset=overrides.pop("chipset", "B650"),
        form_factor=overrides.pop("form_factor", "ATX"),
        memory_type=overrides.pop("memory_type", "DDR5"),
        memory_slots=overrides.pop("memory_slots", 4),
        max_memory_gb=overrides.pop("max_memory_gb", 192),
        **overrides,
    )
    return component


def make_cooler(mpn="COOL-TEST-1", socket_names=("AM4", "AM5"), **overrides):
    component = Component.objects.create(
        mpn=mpn,
        brand=overrides.pop("brand", "Noctua"),
        model=overrides.pop("model", "Test Cooler"),
        msrp=overrides.pop("msrp", Decimal("109.95")),
        category=ComponentCategory.COOLER,
    )
    spec = CoolerSpec.objects.create(
        component=component,
        cooler_type=overrides.pop("cooler_type", CoolerType.AIR),
        tdp_rating_watts=overrides.pop("tdp_rating_watts", 250),
        height_mm=overrides.pop("height_mm", 165),
        **overrides,
    )
    spec.supported_sockets.set([make_socket(name) for name in socket_names])
    return component


def make_ram(mpn="RAM-TEST-1", **overrides):
    component = Component.objects.create(
        mpn=mpn,
        brand=overrides.pop("brand", "Corsair"),
        model=overrides.pop("model", "Vengeance Test"),
        msrp=overrides.pop("msrp", Decimal("89.99")),
        category=ComponentCategory.RAM,
    )
    RamSpec.objects.create(
        component=component,
        memory_type=overrides.pop("memory_type", "DDR5"),
        form_factor=overrides.pop("form_factor", "DIMM"),
        capacity_gb=overrides.pop("capacity_gb", 16),
        module_count=overrides.pop("module_count", 2),
        speed_mts=overrides.pop("speed_mts", 6000),
        cas_latency=overrides.pop("cas_latency", 30),
        height_mm=overrides.pop("height_mm", 35),
        **overrides,
    )
    return component


def proxy_counts():
    return {
        "cpu": Cpu.objects.count(),
        "motherboard": Motherboard.objects.count(),
        "cooler": Cooler.objects.count(),
        "ram": Ram.objects.count(),
        "all": Component.objects.count(),
    }
