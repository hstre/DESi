"""v37.1 - revenue recognition risk check.

A revenue recognition risk is flagged when revenue includes amounts
recognised early / deferred performance obligations. The check reads
explicit structured signals - no fuzzy NLP, no fraud assertion.
"""
from __future__ import annotations


def revenue_recognition_risk(signals: dict) -> bool:
    return bool(signals.get("revenue_deferred_early"))


__all__ = ["revenue_recognition_risk"]
