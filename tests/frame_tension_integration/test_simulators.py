"""Aufgaben 4–7 — every insertion point simulated."""
from __future__ import annotations

from desi.frame_tension_integration.corpus import build_corpus
from desi.frame_tension_integration.enums import InsertionPoint
from desi.frame_tension_integration.simulators import (
    simulate_all_points,
)


def _outcomes():
    return simulate_all_points(build_corpus())


def test_all_four_insertion_points_simulated() -> None:
    outs = _outcomes()
    assert set(outs) == set(InsertionPoint)


def test_each_point_has_one_outcome_per_case() -> None:
    cs = build_corpus()
    outs = _outcomes()
    for point, results in outs.items():
        assert len(results) == len(cs), point.value


def test_outcomes_are_deterministic() -> None:
    a = {
        p.value: [o.to_dict() for o in outs]
        for p, outs in _outcomes().items()
    }
    b = {
        p.value: [o.to_dict() for o in outs]
        for p, outs in _outcomes().items()
    }
    assert a == b


def test_pre_spl_produces_degenerate_results() -> None:
    # When inner and outer are the same combined text, the only
    # possible outcomes are CONFIRMED (signal present) or
    # UNDECIDABLE (signal absent or internally conflicted). The
    # detector cannot disagree with itself, so no TENSION or
    # CONFLICT events should appear at PRE_SPL.
    outs = _outcomes()[InsertionPoint.PRE_SPL]
    forbidden = {
        "frame_inheritance_blocked", "frame_conflict_blocked",
    }
    for o in outs:
        assert o.event not in forbidden, o.case_id


def test_post_spl_pre_frame_produces_meaningful_split() -> None:
    # POST_SPL must produce at least one of each block event over
    # the corpus — otherwise the simulator collapsed.
    outs = _outcomes()[InsertionPoint.POST_SPL_PRE_FRAME]
    events = {o.event for o in outs}
    assert "frame_inheritance_blocked" in events
    assert "frame_conflict_blocked" in events
    assert "frame_undecidable_blocked" in events
