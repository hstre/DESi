"""v37.3 - footnote conflict detection.

Flags a footnote that contradicts the primary statement. The flag
preserves the contradiction; it does not resolve or smooth it.
"""
from __future__ import annotations


def footnote_conflict_flag(signals: dict) -> bool:
    return bool(signals.get("footnote_conflict"))


__all__ = ["footnote_conflict_flag"]
