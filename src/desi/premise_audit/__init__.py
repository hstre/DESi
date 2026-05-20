"""DESi v3.20 — Premise Extractor Signal Audit (read-only)."""
from __future__ import annotations

from .corpus import ChainEntry, all_chains
from .negative_control import ALL_NC_CHAINS, NCChain, NCShape
from .probe import (
    DEAD_KNOB_DELTA,
    PRIMARY_SIGNAL_DELTA,
    SignalProbe,
    run_per_signal_probe,
)
from .report import (
    MIN_CHAIN_COUNT,
    MIN_NC_ACCURACY,
    MIN_TRANSITION_COUNT,
    PremiseAuditReport,
    build_premise_audit_report,
)
from .signals import (
    ExtractionSignals,
    SIGNAL_ORDER,
    SignalName,
    extract_signals,
)

__all__ = [
    "ALL_NC_CHAINS",
    "ChainEntry",
    "DEAD_KNOB_DELTA",
    "ExtractionSignals",
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "NCChain",
    "NCShape",
    "PRIMARY_SIGNAL_DELTA",
    "PremiseAuditReport",
    "SIGNAL_ORDER",
    "SignalName",
    "SignalProbe",
    "all_chains",
    "build_premise_audit_report",
    "extract_signals",
    "run_per_signal_probe",
]
