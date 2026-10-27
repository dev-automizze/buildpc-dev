"""Helpers for keeping socket names consistent across component types."""

# Canonical spelling for sockets whose official name is not simply uppercase.
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


def normalize_socket_name(raw_value):
    """Return a canonical socket name.

    Accepts variants such as "LGA 1700", "lga-1700", "1700", or "socket AM5".
    Unrecognised values are returned stripped but otherwise unchanged so a
    human can fix them later instead of silently losing data.
    """
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
