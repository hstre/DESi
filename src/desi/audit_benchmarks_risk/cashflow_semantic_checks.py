"""v37.1 - cashflow-vs-narrative semantic check.

A cashflow tension is flagged when a positive cash-generation
narrative sits alongside an adjusted (one-off-excluding) cashflow -
the story claims strength the adjusted numbers do not unambiguously
support. The flag preserves the tension; it does not resolve it.
"""
from __future__ import annotations


def cashflow_vs_narrative_risk(signals: dict) -> bool:
    return bool(signals.get("cashflow_adjusted")) and bool(
        signals.get("narrative_cash_positive")
    )


__all__ = ["cashflow_vs_narrative_risk"]
