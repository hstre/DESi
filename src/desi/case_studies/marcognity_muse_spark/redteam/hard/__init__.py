"""Hard epistemic-failure benchmark: raw, embedded, adversarial items with
multi-label scoring (precision/recall/F1). Built to actually discriminate between
reviewers, unlike the telegraphed pilot excerpts.

Note on DESi: the rule-based ``DesiReviewer`` operates on pre-extracted, typed claims
from the case-study fixture — it has no raw-text front-end and therefore does NOT
run on these raw items. DESi's place is a deterministic gate AFTER an LLM extracts
claims, not a raw-text competitor. This benchmark measures the frontier LLMs' real
ceiling on hard epistemic detection.
"""
from __future__ import annotations

from . import items, prompt, score

__all__ = ["items", "prompt", "score"]
