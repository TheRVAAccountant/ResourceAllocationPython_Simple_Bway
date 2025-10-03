"""Theme utilities for accessible, semantic colors in the GUI.

Provides light/dark tuples compatible with CustomTkinter. Tuples are
ordered as (light_mode_color, dark_mode_color).

Only UI colors are defined here; there is no business logic.
"""

from __future__ import annotations

Color = str | tuple[str, str]

# Semantic accent colors for dashboard metrics
ACCENTS: dict[str, tuple[str, str]] = {
    # Metrics
    "total_vehicles": ("#1E3A8A", "#93C5FD"),  # deep blue / soft light blue
    "total_drivers": ("#166534", "#86EFAC"),  # dark green / mint green
    "allocated": ("#92400E", "#F59E0B"),  # brown-orange / amber
    "allocation_rate": ("#6B21A8", "#D8B4FE"),  # deep purple / light purple
    "unallocated": ("#991B1B", "#F87171"),  # dark red / light red
    "avg_per_driver": ("#0E7490", "#67E8F9"),  # teal / light cyan
    "processing_time": ("#374151", "#D1D5DB"),  # slate / light gray
    "last_run": ("#9D174D", "#F9A8D4"),  # dark rose / light pink
}

# Status indicator colors
STATUS: dict[str, tuple[str, str]] = {
    "active": ("#166534", "#22C55E"),  # dark green / emerald
    "disabled": ("#92400E", "#F59E0B"),  # brown-orange / amber
    "inactive": ("#991B1B", "#EF4444"),  # dark red / red
    "error": ("#991B1B", "#EF4444"),  # alias
}

DEFAULT_ACCENT: tuple[str, str] = ("#2563EB", "#93C5FD")  # blue / light blue


def get_accent(name: str) -> tuple[str, str]:
    """Return a semantic accent color tuple.

    Falls back to DEFAULT_ACCENT if the key is unknown.
    """
    return ACCENTS.get(name, DEFAULT_ACCENT)


def get_status_color(name: str) -> tuple[str, str]:
    """Return a status color tuple. Name is case-insensitive."""
    return STATUS.get(name.lower(), STATUS["inactive"])  # sensible default


def resolve_color(value: Color) -> Color:
    """Resolve a color value that may be semantic or literal.

    - If `value` is a semantic key in ACCENTS/STATUS, return the tuple.
    - Otherwise return `value` unchanged (string literal or tuple).
    """
    if isinstance(value, str):
        if value in ACCENTS:
            return ACCENTS[value]
        if value.lower() in STATUS:
            return STATUS[value.lower()]
    return value
