"""GSM-Symbolic G1 - deterministic illustrative prediction fixtures.

These are NOT model outputs. They are fixed, deterministic prediction
sets whose only purpose is to exercise and validate the invariance
metric definitions in ``scoring.py`` (every metric has a fixture that
drives it to a known value). No empirical claim about any model - or
about DESi - is made or implied here; the real solver arms arrive at the
live G2 stage.

The constant ``_WRONG`` marker is deliberately not a valid numeric
answer, so it can never collide with a gold value.
"""
from __future__ import annotations

from .groups import build_groups
from .normalizer import all_normalized_tasks
from .scoring import Predictions

_WRONG = "__wrong__"


def all_correct_predictions() -> Predictions:
    """Every instance correct -> strict=1, accuracy=1."""
    return {t.task_id: t.answer for t in all_normalized_tasks()}


def first_only_correct_predictions() -> Predictions:
    """Only the first instance of each template is correct; the rest are
    wrong with one shared wrong answer -> mixed groups (strict=0,
    consistency=0) with a stable error (error_stability=1)."""
    preds: Predictions = {}
    for g in build_groups():
        for i, t in enumerate(g.tasks):
            preds[t.task_id] = t.answer if i == 0 else _WRONG
    return preds


def constant_wrong_predictions() -> Predictions:
    """Every instance wrong with one shared answer -> all-wrong groups
    (consistency=1) with a stable error (error_stability=1)."""
    return {t.task_id: _WRONG for t in all_normalized_tasks()}


def drifting_wrong_predictions() -> Predictions:
    """Every instance wrong with a unique answer -> all-wrong groups
    (consistency=1) but a drifting error (error_stability=0)."""
    return {
        t.task_id: f"{_WRONG}{t.task_id}"
        for t in all_normalized_tasks()
    }


def noop_fragile_predictions() -> Predictions:
    """Correct everywhere except P2 noop instances -> isolates a
    positive noop_gap with no other source of error."""
    preds: Predictions = {}
    for t in all_normalized_tasks():
        if t.variant == "p2" and t.clause_role == "noop":
            preds[t.task_id] = _WRONG
        else:
            preds[t.task_id] = t.answer
    return preds


__all__ = [
    "all_correct_predictions",
    "constant_wrong_predictions",
    "drifting_wrong_predictions",
    "first_only_correct_predictions",
    "noop_fragile_predictions",
]
