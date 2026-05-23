"""Closed taxonomies for v3.12 — Aufgabe 2."""
from __future__ import annotations

from enum import Enum


class InsertionPoint(str, Enum):
    """Where in the DESi pipeline the v3.11 FrameTensionLayer
    would be invoked. Exactly four points — no others."""

    PRE_SPL                  = "pre_spl"
    POST_SPL_PRE_FRAME       = "post_spl_pre_frame"
    POST_FRAME_PRE_ROUTING   = "post_frame_pre_routing"
    POST_ROUTING             = "post_routing"


class CorpusOrigin(str, Enum):
    """Provenance of a simulation corpus case — for the audit
    trail only; no decision logic depends on the origin."""

    V38_INHERITANCE   = "v38_inheritance"
    V39_MANIPULATION  = "v39_manipulation"
    V310_TENSION_AUDIT = "v310_tension_audit"
    V311_RUNTIME      = "v311_runtime"


__all__ = ["CorpusOrigin", "InsertionPoint"]
