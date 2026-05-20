"""v7.3 — windowed memory primitives over the
1000-step social-drift trajectory."""
from __future__ import annotations


SHORT_WINDOW: int = 100
LONG_WINDOW:  int = 400


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
    "LONG_WINDOW", "SHORT_WINDOW",
    "early_window", "late_window",
    "mid_window",
]
