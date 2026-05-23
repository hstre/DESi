"""v37.1 - going concern risk analysis.

A going concern risk is flagged when there is explicit going-concern
doubt alongside a binding debt covenant. The flag marks uncertainty;
it never asserts insolvency.
"""
from __future__ import annotations


def going_concern_risk(signals: dict) -> bool:
    return bool(signals.get("going_concern_doubt")) and bool(
        signals.get("debt_covenant")
    )


__all__ = ["going_concern_risk"]
