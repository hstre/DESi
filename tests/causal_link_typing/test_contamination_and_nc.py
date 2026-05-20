"""Aufgaben 5 + 6 — contamination + negative control."""
from __future__ import annotations

from desi.causal_link_typing import (
    ALLOWED_LINK_TYPES,
    LinkType,
    negative_control_count,
    run_contamination_probe,
    run_negative_controls,
)


def test_allowed_link_types_are_the_three_specified() -> None:
    assert ALLOWED_LINK_TYPES == frozenset({
        LinkType.PHYSICAL_CAUSAL,
        LinkType.INSTITUTIONAL_CAUSAL,
        LinkType.LOGICAL_IMPLICATION,
    })


def test_contamination_probe_covers_every_corpus() -> None:
    r = run_contamination_probe()
    expected = {
        "v23_multistep",
        "v314_heldout",
        "v315_adversarial",
        "v316_suspended",
    }
    assert set(r.per_corpus) == expected


def test_contamination_is_deterministic() -> None:
    a = run_contamination_probe()
    b = run_contamination_probe()
    assert a.to_dict() == b.to_dict()


def test_negative_control_count_meets_minimum() -> None:
    assert negative_control_count() >= 30


def test_negative_control_accuracy_meets_threshold() -> None:
    _outs, acc = run_negative_controls()
    assert acc >= 0.95


def test_every_negative_control_link_classified() -> None:
    outs, _ = run_negative_controls()
    for o in outs:
        for label in o.actual:
            assert label in {t.value for t in LinkType}
