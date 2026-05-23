"""v8.3 — windowed memory over the 2000-step
persistent-pressure trajectory."""
from __future__ import annotations


SHORT_WINDOW: int = 200


def early_window(seq: tuple) -> tuple:
    return seq[:SHORT_WINDOW]


def late_window(seq: tuple) -> tuple:
    return seq[-SHORT_WINDOW:]


def mid_window(seq: tuple) -> tuple:
    n = len(seq)
    half = SHORT_WINDOW // 2
    mid = n // 2
    return seq[mid - half:mid + half]


__all__ = [
    "SHORT_WINDOW", "early_window",
    "late_window", "mid_window",
]
