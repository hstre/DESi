"""v37.3 - management spin and 'too smooth' narrative detection.

Flags management spin and narratives that read 'too smooth' to be
unconditionally trusted. These are epistemic warning markers, not
accusations.
"""
from __future__ import annotations


def management_spin_flag(signals: dict) -> bool:
    return bool(signals.get("management_spin"))


def too_smooth_flag(signals: dict) -> bool:
    return bool(signals.get("too_smooth"))


__all__ = ["management_spin_flag", "too_smooth_flag"]
