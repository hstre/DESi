"""HARD2 — a harder epistemic-failure benchmark (8 flags incl. causal overreach,
significance-vs-importance, base-rate neglect). Reuses ``..hard.score`` (generic
over an item set). Built to push even strong models below the saturation ceiling of
the 5-flag set.
"""
from __future__ import annotations

from . import items, prompt

__all__ = ["items", "prompt"]
