"""v6.3 — closed-window memory primitives.

A short-window (last 50 steps) and a long-window
(last 200 steps) memory over the trajectory. Both
are pure projections from the deterministic
trajectory; no mutable state, no PRNG.
"""
from __future__ import annotations


SHORT_WINDOW: int = 50
LONG_WINDOW:  int = 200


def short_window(
    seq: tuple, current_step: int,
) -> tuple:
    """Last SHORT_WINDOW items leading up to and
    including current_step (zero-indexed)."""
    end = current_step + 1
    start = max(0, end - SHORT_WINDOW)
    return seq[start:end]


def long_window(
    seq: tuple, current_step: int,
) -> tuple:
    """Last LONG_WINDOW items up to and including
    current_step."""
    end = current_step + 1
    start = max(0, end - LONG_WINDOW)
    return seq[start:end]


def early_window(seq: tuple) -> tuple:
    return seq[:SHORT_WINDOW]


def late_window(seq: tuple) -> tuple:
    return seq[-SHORT_WINDOW:]


__all__ = [
    "LONG_WINDOW", "SHORT_WINDOW",
    "early_window", "late_window",
    "long_window", "short_window",
]
