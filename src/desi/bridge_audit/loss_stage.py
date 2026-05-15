"""Closed enumeration of loss stages — Aufgabe 2.

Each ``BridgeEntryTrace`` is classified into **exactly one**
:class:`LossStage`. The nine values below form a partition that
covers every observable outcome of the v1.9 evaluation pipeline.
"""
from __future__ import annotations

from enum import Enum


class LossStage(str, Enum):
    NO_LOSS = "no_loss"
    PARSER_LOSS = "parser_loss"
    AUDIT_REJECT_LOSS = "audit_reject_loss"
    BRIDGE_MISSING_LOSS = "bridge_missing_loss"
    CONSILIUM_VETO_LOSS = "consilium_veto_loss"
    RESOLVER_NOT_REACHED = "resolver_not_reached"
    RESOLVER_ZERO_DEPTH = "resolver_zero_depth"
    CYCLE_NOT_RECOGNIZED = "cycle_not_recognized"
    UNKNOWN_LOSS = "unknown_loss"


__all__ = ["LossStage"]
