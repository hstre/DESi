"""DESi control plane — taint-safe Layer-9 updates and control-plane integrity.

A drifting model must not be able to silently mutate the authoritative state or
change goals, roles, method selection, or release rules. Three deterministic
pieces enforce that:

* ``model`` — the authority + taint schema (data/control separation; taint
  propagation that cannot be laundered by rewriting).
* ``gate`` — the deterministic state-update gate: no model output reaches the
  authoritative state except through a fixed check pipeline.
* ``benchmark`` — an adversarial control-plane benchmark that attacks the
  control, not the answer.

Plus ``directive`` — the turn-level re-anchor compiled from authoritative
state rather than carried as a free-form prompt.
"""
from __future__ import annotations

from .benchmark import VIOLATIONS, run_control_plane_benchmark
from .directive import compile_directive, default_contamination_directive
from .gate import GateDecision, LedgerSink, StateUpdateGate
from .model import (
    AUTHORITY_LEVELS,
    CONTROL_SENSITIVE_KINDS,
    EXPOSURES,
    ORIGINS,
    TAINTS,
    StateObject,
    authority_at_least,
    clear_taint,
    ingest_model_output,
    propagate,
)

__all__ = [
    "AUTHORITY_LEVELS",
    "CONTROL_SENSITIVE_KINDS",
    "EXPOSURES",
    "GateDecision",
    "LedgerSink",
    "ORIGINS",
    "StateObject",
    "StateUpdateGate",
    "TAINTS",
    "VIOLATIONS",
    "authority_at_least",
    "clear_taint",
    "compile_directive",
    "default_contamination_directive",
    "ingest_model_output",
    "propagate",
    "run_control_plane_benchmark",
]
