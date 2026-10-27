"""CSV import helpers for component data.

Each row is imported inside its own savepoint so a single bad row cannot leave
the database half-written, and cannot stop the remaining good rows.
"""

import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import (
    Component,
    ComponentCategory,
    CoolerSpec,
    CoolerType,
    CpuSpec,
    MemoryType,
    MotherboardFormFactor,
    MotherboardSpec,
    Socket,
)
from .sockets import normalize_socket_name

logger = logging.getLogger(__name__)


class ImportRowError(Exception):
    """Raised when a CSV row cannot be imported."""


def _value(row, key):
    value = row.get(key, "")
    return "" if value is None else str(value).strip()


def _required(row, key):
    value = _value(row, key)
    if not value:
        raise ImportRowError(f"missing value for '{key}'")
    return value


def _parse_bool(row, key, default=False):
    value = _value(row, key).lower()
    if not value:
        return default
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    raise ImportRowError(f"'{key}' must be true/false, got '{value}'")


def _parse_int(row, key, required=True):
    value = _value(row, key)
    if not value:
        if required:
            raise ImportRowError(f"missing value for '{key}'")
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ImportRowError(f"'{key}' must be an integer, got '{value}'") from exc
    if parsed < 0:
        raise ImportRowError(f"'{key}' cannot be negative, got '{value}'")
    return parsed


def _parse_float(row, key, required=False):
    value = _value(row, key)
    if not value:
        if required:
            raise ImportRowError(f"missing value for '{key}'")
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ImportRowError(f"'{key}' must be a number, got '{value}'") from exc


def _parse_decimal(row, key, required=True):
    value = _value(row, key)
    if not value:
        if required:
            raise ImportRowError(f"missing value for '{key}'")
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ImportRowError(f"'{key}' must be a decimal number, got '{value}'") from exc


def _resolve_socket(raw_name):
    name = normalize_socket_name(raw_name)
    if not name:
        raise ImportRowError("'socket' is required")
    socket, _ = Socket.objects.get_or_create(name=name)
    return socket


def _resolve_sockets(raw_names):
    parts = [part for part in raw_names.replace("|", ",").replace(";", ",").split(",")]
    names = [normalize_socket_name(part) for part in parts]
    names = list(dict.fromkeys(name for name in names if name))  # de-dupe, keep order
    if not names:
        raise ImportRowError("'supportedSockets' must list at least one socket")
    sockets = []
    for name in names:
        socket, _ = Socket.objects.get_or_create(name=name)
        sockets.append(socket)
    return sockets


def _component(row, category):
    mpn = _required(row, "mpn")
    existing = Component.objects.filter(mpn=mpn).first()
    if existing and existing.category != category:
        raise ImportRowError(
            f"mpn '{mpn}' already exists as {existing.category}, not {category}"
        )

    component, _ = Component.objects.update_or_create(
        mpn=mpn,
        defaults={
            "brand": _required(row, "brand"),
            "model": _required(row, "model"),
            "msrp": _parse_decimal(row, "msrp"),
            "category": category,
        },
    )
    return component


def _import_cpu(row):
    component = _component(row, ComponentCategory.CPU)
    CpuSpec.objects.update_or_create(
        component=component,
        defaults={
            "socket": _resolve_socket(_required(row, "socket")),
            "core_count": _parse_int(row, "coreCount"),
            "thread_count": _parse_int(row, "threadCount"),
            "base_clock_ghz": _parse_float(row, "baseClockGhz", required=True),
            "boost_clock_ghz": _parse_float(row, "boostClockGhz", required=True),
            "tdp_watts": _parse_int(row, "tdpWatts"),
            "max_power_watts": _parse_int(row, "maxPowerWatts", required=False),
            "has_integrated_gpu": _parse_bool(row, "hasIntegratedGpu"),
            "included_cooler": _parse_bool(row, "includedCooler"),
        },
    )


def _normalize_form_factor(raw_value):
    value = str(raw_value or "").strip()
    aliases = {
        "atx": MotherboardFormFactor.ATX,
        "micro atx": MotherboardFormFactor.MICRO_ATX,
        "micro-atx": MotherboardFormFactor.MICRO_ATX,
        "matx": MotherboardFormFactor.MICRO_ATX,
        "mini itx": MotherboardFormFactor.MINI_ITX,
        "mini-itx": MotherboardFormFactor.MINI_ITX,
        "mitx": MotherboardFormFactor.MINI_ITX,
        "e-atx": MotherboardFormFactor.E_ATX,
        "eatx": MotherboardFormFactor.E_ATX,
        "eeb": MotherboardFormFactor.EEB,
        "deep micro-atx": MotherboardFormFactor.DEEP_MICRO_ATX,
    }
    normalized = aliases.get(value.lower())
    if not normalized:
        valid = ", ".join(MotherboardFormFactor.values)
        raise ImportRowError(f"'formFactor' must be one of: {valid}; got '{value}'")
    return normalized


def _normalize_memory_type(raw_value):
    value = str(raw_value or "").strip().upper()
    if value not in MemoryType.values:
        valid = ", ".join(MemoryType.values)
        raise ImportRowError(f"'memoryType' must be one of: {valid}; got '{raw_value}'")
    return value


def _import_motherboard(row):
    component = _component(row, ComponentCategory.MOTHERBOARD)
    MotherboardSpec.objects.update_or_create(
        component=component,
        defaults={
            "chipset": _value(row, "chipset"),
            "socket": _resolve_socket(_required(row, "socket")),
            "form_factor": _normalize_form_factor(_required(row, "formFactor")),
            "memory_type": _normalize_memory_type(_required(row, "memoryType")),
            "memory_slots": _parse_int(row, "memorySlots"),
            "max_memory_gb": _parse_int(row, "maxMemoryGb"),
            "m2_slots": _parse_int(row, "m2Slots", required=False) or 0,
            "sata_slots": _parse_int(row, "sataSlots", required=False) or 0,
            "has_wifi": _parse_bool(row, "hasWifi"),
            "pcie_lanes": _value(row, "pcieLanes"),
            "vrm_phases": _value(row, "vrmPhases"),
        },
    )


def _normalize_cooler_type(raw_value):
    value = str(raw_value or "").strip().lower()
    aliases = {
        "air": CoolerType.AIR,
        "aio": CoolerType.AIO,
        "liquid": CoolerType.AIO,
        "aio liquid": CoolerType.AIO,
        "water": CoolerType.AIO,
        "passive": CoolerType.PASSIVE,
        "fanless": CoolerType.PASSIVE,
    }
    normalized = aliases.get(value)
    if not normalized:
        valid = ", ".join(choice.label for choice in CoolerType)
        raise ImportRowError(f"'coolerType' must be one of: {valid}; got '{raw_value}'")
    return normalized


def _import_cooler(row):
    component = _component(row, ComponentCategory.COOLER)
    supported_sockets = _resolve_sockets(_required(row, "supportedSockets"))
    spec, _ = CoolerSpec.objects.update_or_create(
        component=component,
        defaults={
            "cooler_type": _normalize_cooler_type(_value(row, "coolerType") or CoolerType.AIR),
            "tdp_rating_watts": _parse_int(row, "tdpRatingWatts"),
            "height_mm": _parse_int(row, "heightMm", required=False),
            "ram_clearance_mm": _parse_int(row, "ramClearanceMm", required=False),
            "radiator_size_mm": _parse_int(row, "radiatorSizeMm", required=False),
            "radiator_thickness_mm": _parse_int(row, "radiatorThicknessMm", required=False),
            "radiator_length_mm": _parse_int(row, "radiatorLengthMm", required=False),
            "radiator_width_mm": _parse_int(row, "radiatorWidthMm", required=False),
            "fan_count": _parse_int(row, "fanCount", required=False) or 1,
            "fan_size_mm": _parse_int(row, "fanSizeMm", required=False),
            "noise_db_max": _parse_float(row, "noiseDbMax"),
            "weight_g": _parse_int(row, "weightG", required=False),
            "power_connector": _value(row, "powerConnector"),
        },
    )
    spec.supported_sockets.set(supported_sockets)


_IMPORTERS = {
    ComponentCategory.CPU: _import_cpu,
    ComponentCategory.MOTHERBOARD: _import_motherboard,
    ComponentCategory.COOLER: _import_cooler,
}


def import_csv(reader, category):
    """Import rows from a csv.DictReader.

    Returns ``(success_count, errors)`` where errors is a list of human-readable
    messages that include the CSV row number.
    """
    importer = _IMPORTERS.get(category)
    if importer is None:
        valid = ", ".join(_IMPORTERS)
        raise ImportRowError(f"Unsupported component type '{category}'. Choose one of: {valid}")

    success_count = 0
    errors = []
    for line_number, row in enumerate(reader, start=2):
        try:
            with transaction.atomic():
                importer(row)
            success_count += 1
        except (ImportRowError, KeyError, ValueError, InvalidOperation) as exc:
            errors.append(f"Row {line_number}: {exc}")
        except Exception as exc:  # pragma: no cover - defensive, should not happen
            logger.exception("Unexpected error importing row %s", line_number)
            errors.append(f"Row {line_number}: unexpected error: {exc}")
    return success_count, errors
