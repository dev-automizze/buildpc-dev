from django.db import models


class Socket(models.Model):
    """Canonical CPU socket, shared by CPUs, motherboards, and coolers."""

    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ComponentCategory(models.TextChoices):
    CPU = "CPU", "CPU"
    MOTHERBOARD = "Motherboard", "Motherboard"
    COOLER = "Cooler", "Cooler"


class CoolerType(models.TextChoices):
    AIR = "Air", "Air"
    AIO = "AIO", "AIO Liquid"
    PASSIVE = "Passive", "Passive"


class MotherboardFormFactor(models.TextChoices):
    ATX = "ATX", "ATX"
    MICRO_ATX = "Micro-ATX", "Micro-ATX"
    MINI_ITX = "Mini-ITX", "Mini-ITX"
    E_ATX = "E-ATX", "E-ATX"
    EEB = "EEB", "EEB"
    DEEP_MICRO_ATX = "Deep Micro-ATX", "Deep Micro-ATX"


class MemoryType(models.TextChoices):
    DDR4 = "DDR4", "DDR4"
    DDR5 = "DDR5", "DDR5"


class CategoryManager(models.Manager):
    """Manager that scopes a proxy model to one component category."""

    def __init__(self, category, *args, **kwargs):
        self.category = category
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(category=self.category)


class Component(models.Model):
    mpn = models.CharField(max_length=100, unique=True, help_text="Manufacturer Part Number")
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    msrp = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=50,
        choices=ComponentCategory.choices,
        default=ComponentCategory.CPU,
        db_index=True,
    )

    class Meta:
        verbose_name = "Component"
        verbose_name_plural = "All Components"  # Places master list at the top!

    def __str__(self):
        return f"{self.brand} {self.model} ({self.mpn})"


class CpuSpec(models.Model):
    component = models.OneToOneField(Component, on_delete=models.CASCADE, related_name="cpu_spec")
    socket = models.ForeignKey(Socket, on_delete=models.PROTECT, related_name="cpu_specs")
    core_count = models.IntegerField()
    thread_count = models.IntegerField()
    base_clock_ghz = models.FloatField()
    boost_clock_ghz = models.FloatField()
    tdp_watts = models.IntegerField()
    max_power_watts = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sustained package power (AMD PPT / Intel PL2). Falls back to TDP when empty.",
    )
    has_integrated_gpu = models.BooleanField(default=False)
    included_cooler = models.BooleanField(default=False)

    @property
    def effective_power_watts(self):
        """Power figure used for cooler matching, with TDP as the fallback."""
        return self.max_power_watts or self.tdp_watts

    def __str__(self):
        return f"Specs for {self.component.model}"


class MotherboardSpec(models.Model):
    component = models.OneToOneField(Component, on_delete=models.CASCADE, related_name="motherboard_spec")
    chipset = models.CharField(max_length=50, default="", help_text="e.g., B650, Z790, X670E")
    socket = models.ForeignKey(Socket, on_delete=models.PROTECT, related_name="motherboard_specs")
    form_factor = models.CharField(
        max_length=20,
        choices=MotherboardFormFactor.choices,
        help_text="e.g., ATX, Micro-ATX, Mini-ITX",
    )
    memory_type = models.CharField(
        max_length=10,
        choices=MemoryType.choices,
        help_text="e.g., DDR4, DDR5",
    )
    memory_slots = models.IntegerField()
    max_memory_gb = models.IntegerField()
    m2_slots = models.IntegerField(default=0, help_text="Number of M.2 NVMe slots")
    sata_slots = models.IntegerField(default=0, help_text="Number of SATA ports")
    has_wifi = models.BooleanField(default=False)
    pcie_lanes = models.CharField(max_length=150, blank=True, null=True, help_text="e.g., 1x PCIe 5.0 x16, 2x PCIe 4.0 x4")
    vrm_phases = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 16+2+2 Phases or 90A Power Stage")

    def __str__(self):
        return f"Specs for {self.component.model}"


class CoolerSpec(models.Model):
    component = models.OneToOneField(Component, on_delete=models.CASCADE, related_name="cooler_spec")
    cooler_type = models.CharField(
        max_length=20,
        choices=CoolerType.choices,
        default=CoolerType.AIR,
    )
    supported_sockets = models.ManyToManyField(Socket, related_name="cooler_specs")

    tdp_rating_watts = models.PositiveIntegerField(
        help_text="Manufacturer rated heat dissipation in watts."
    )

    # Air cooler fitment
    height_mm = models.FloatField(
        null=True,
        blank=True,
        help_text="Air cooler height in mm. Leave empty for liquid coolers.",
    )
    ram_clearance_mm = models.FloatField(
        null=True,
        blank=True,
        help_text="Clearance under the heatsink for memory modules, in mm.",
    )

    # Liquid cooler fitment
    radiator_size_mm = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Radiator size in mm, e.g. 240, 280, 360. Leave empty for air coolers.",
    )
    radiator_thickness_mm = models.FloatField(null=True, blank=True)
    radiator_length_mm = models.FloatField(null=True, blank=True)
    radiator_width_mm = models.FloatField(null=True, blank=True)

    # Fans and general specs
    fan_count = models.PositiveIntegerField(default=1)
    fan_size_mm = models.FloatField(null=True, blank=True)
    noise_db_max = models.FloatField(null=True, blank=True, help_text="Maximum noise level in dBA.")
    weight_g = models.PositiveIntegerField(null=True, blank=True)
    power_connector = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="e.g., 4-pin PWM, SATA power, Molex",
    )

    def __str__(self):
        return f"Specs for {self.component.model}"


# Proxy Models for Admin Menu Separation
class Cpu(Component):
    objects = CategoryManager(ComponentCategory.CPU)

    class Meta:
        proxy = True
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"


class Motherboard(Component):
    objects = CategoryManager(ComponentCategory.MOTHERBOARD)

    class Meta:
        proxy = True
        verbose_name = "Motherboard"
        verbose_name_plural = "Motherboards"


class Cooler(Component):
    objects = CategoryManager(ComponentCategory.COOLER)

    class Meta:
        proxy = True
        verbose_name = "Cooler"
        verbose_name_plural = "Coolers"
