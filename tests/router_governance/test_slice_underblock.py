"""Under-block red-team — the gate's coverage is bounded by signals, not by check logic.

These tests pin the completeness-critic result: each named wrong-but-passing family genuinely slips
through (so the limit is real and visible, not hidden), and each is caught the moment its missing
signal is supplied (so the check logic is sound). The honest conclusion: closing these means better
upstream signals / a richer claim model — not fixing the gate's logic.
"""
from __future__ import annotations

from desi_router.governance.benchmark.underblock import (
    CASES,
    IRREDUCIBLE,
    evaluate,
)


def test_clean_control_survives_gate_is_not_blocking_everything():
    rep = evaluate()
    assert rep["clean_control_survives"] is True


def test_every_named_underblock_family_genuinely_slips_through():
    # if one of these stopped surviving, the catalogue would be stale — the point is they are REAL
    rep = evaluate()
    assert {r["key"] for r in rep["rows"]} == {c.key for c in CASES}
    for r in rep["rows"]:
        assert r["survives"] is True, f"{r['key']} no longer slips through — update the catalogue"


def test_all_non_irreducible_misses_are_caught_once_the_signal_is_fed():
    # the load-bearing claim: the misses are SIGNAL-quality limits, not logic holes
    rep = evaluate()
    assert rep["all_misses_are_signal_bounded"] is True
    for r in rep["rows"]:
        assert r["caught_when_fed"] is True


def test_classifications_are_the_three_honest_kinds():
    kinds = {c.classification for c in CASES}
    assert kinds <= {"irreducible_no_signal", "signal_quality_upstream", "data_model_gap"}
    # at least one irreducible floor case is documented (the no-opposition confident-wrong slice)
    assert any(c.classification == IRREDUCIBLE for c in CASES)
