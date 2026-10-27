# Step 2 of the socket normalisation: data only.
#
# Copies each spec's old socket string into the new socket_ref foreign key and
# normalises the handful of enum values that drifted in the old CSV data.
# Kept separate from schema changes for PostgreSQL's pending-trigger rules.

from django.db import migrations


# Frozen copy of components.sockets.normalize_socket_name. Migrations must not
# import application code because that code can change later.
_CANONICAL_SOCKETS = {
    "am4": "AM4",
    "am5": "AM5",
    "tr4": "TR4",
    "str5": "sTR5",
    "tr5": "sTR5",
    "sp3": "SP3",
    "sp5": "SP5",
    "sp6": "SP6",
}

_FORM_FACTORS = {
    "atx": "ATX",
    "micro atx": "Micro-ATX",
    "micro-atx": "Micro-ATX",
    "matx": "Micro-ATX",
    "mini itx": "Mini-ITX",
    "mini-itx": "Mini-ITX",
    "mitx": "Mini-ITX",
    "e-atx": "E-ATX",
    "eatx": "E-ATX",
    "eeb": "EEB",
    "deep micro-atx": "Deep Micro-ATX",
}


def _normalize_socket_name(raw_value):
    value = str(raw_value or "").strip()
    if not value:
        return ""

    compact = value.lower().replace(" ", "").replace("_", "").replace("-", "")
    if compact.startswith("socket"):
        compact = compact[len("socket"):]

    if compact.startswith("lga") and compact[3:].isdigit():
        return f"LGA{compact[3:]}"

    if compact.isdigit() and len(compact) == 4:
        return f"LGA{compact}"

    return _CANONICAL_SOCKETS.get(compact, value)


def populate_sockets_and_normalize(apps, schema_editor):
    Socket = apps.get_model("components", "Socket")
    CpuSpec = apps.get_model("components", "CpuSpec")
    MotherboardSpec = apps.get_model("components", "MotherboardSpec")

    seeded = [
        "AM4", "AM5", "LGA1150", "LGA1151", "LGA1200", "LGA1700", "LGA1851",
        "LGA2066", "LGA4677", "LGA4710", "SP3", "SP5", "SP6", "TR4", "sTR5",
        "Unknown",
    ]
    for name in seeded:
        Socket.objects.get_or_create(name=name)

    for model in (CpuSpec, MotherboardSpec):
        for spec in model.objects.all().only("id", "socket"):
            name = _normalize_socket_name(spec.socket) or "Unknown"
            socket, _ = Socket.objects.get_or_create(name=name)
            spec.socket_ref_id = socket.pk
            spec.save(update_fields=["socket_ref"])

    for spec in MotherboardSpec.objects.all().only("id", "form_factor", "memory_type"):
        changed = []

        form_factor = _FORM_FACTORS.get(str(spec.form_factor or "").strip().lower())
        if form_factor and form_factor != spec.form_factor:
            spec.form_factor = form_factor
            changed.append("form_factor")

        memory_type = str(spec.memory_type or "").strip().upper().replace(" ", "")
        if memory_type and memory_type != spec.memory_type:
            spec.memory_type = memory_type
            changed.append("memory_type")

        if changed:
            spec.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0005_socket_foundation'),
    ]

    operations = [
        migrations.RunPython(populate_sockets_and_normalize, migrations.RunPython.noop),
    ]
