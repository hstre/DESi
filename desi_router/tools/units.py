"""Deterministic unit-conversion tool (length, mass, temperature).

Parses "<x> <unit> to <unit>" / "<x> <unit> in <unit>" and converts within a
category. Factors are exact constants to a base unit; temperature is handled
explicitly. Unknown units or cross-category conversions raise ValueError.
"""
from __future__ import annotations

import re

# unit -> factor to base (length base = metre, mass base = gram)
_LENGTH = {
    "m": 1.0, "meter": 1.0, "meters": 1.0, "metre": 1.0, "metres": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
    "cm": 0.01, "mm": 0.001,
    "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
    "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
    "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
}
_MASS = {
    "g": 1.0, "gram": 1.0, "grams": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
    "mg": 0.001, "t": 1_000_000.0, "tonne": 1_000_000.0, "tonnes": 1_000_000.0,
    "lb": 453.59237, "lbs": 453.59237, "pound": 453.59237, "pounds": 453.59237,
    "oz": 28.349523125, "ounce": 28.349523125, "ounces": 28.349523125,
}
_TEMP = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}

# Longest alternative first: with "to|in|into", 'in' matches inside 'into' and
# the leftover 'to' is parsed as the target unit ("5 km into miles" -> km->to).
_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*(?:into|to|in)\s*([a-zA-Z]+)", re.I
)


def _to_celsius(x: float, u: str) -> float:
    if u in ("c", "celsius"):
        return x
    if u in ("f", "fahrenheit"):
        return (x - 32) * 5 / 9
    return x - 273.15  # kelvin


def _from_celsius(c: float, u: str) -> float:
    if u in ("c", "celsius"):
        return c
    if u in ("f", "fahrenheit"):
        return c * 9 / 5 + 32
    return c + 273.15


def _round(v: float) -> float | int:
    r = round(v, 4)
    return int(r) if float(r).is_integer() else r


def convert_units(text: str) -> float | int:
    m = _RE.search(text)
    if not m:
        raise ValueError("no '<x> <unit> to <unit>' expression found")
    x, u1, u2 = float(m.group(1)), m.group(2).lower(), m.group(3).lower()

    if u1 in _TEMP and u2 in _TEMP:
        return _round(_from_celsius(_to_celsius(x, u1), u2))
    for table in (_LENGTH, _MASS):
        if u1 in table and u2 in table:
            return _round(x * table[u1] / table[u2])
    raise ValueError(f"unknown or cross-category units: {u1!r} -> {u2!r}")
