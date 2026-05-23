"""Tests for v3.7 candidate generation + scoring (Aufgaben 2 + 4 + 5)."""
from __future__ import annotations

from desi.frame_disambiguator_probe import (
    extract_polysemy_targets,
    extract_thermo_counter_set,
    generate_candidates,
    score_all,
)


def test_at_least_ten_candidates_generated() -> None:
    """Aufgabe 2 — candidate_count >= 10."""
    targets = extract_polysemy_targets()
    candidates = generate_candidates(targets)
    assert len(candidates) >= 10


def test_every_candidate_carries_anchor() -> None:
    """Every candidate must include the polysemy anchor 'entropy'."""
    targets = extract_polysemy_targets()
    for c in generate_candidates(targets):
        assert "entropy" in c.tokens


def test_no_singleton_candidates() -> None:
    """Aufgabe 2 — size = 2 oder 3, niemals 1."""
    targets = extract_polysemy_targets()
    for c in generate_candidates(targets):
        assert 2 <= len(c.tokens) <= 3


def test_scoring_returns_unit_interval_precision_and_coverage() -> None:
    targets = extract_polysemy_targets()
    counters = extract_thermo_counter_set()
    candidates = generate_candidates(targets)
    scores = score_all(candidates, targets, counters)
    for s in scores:
        assert 0.0 <= s.info_precision <= 1.0
        assert 0.0 <= s.coverage <= 1.0


def test_scoring_is_deterministic() -> None:
    targets = extract_polysemy_targets()
    counters = extract_thermo_counter_set()
    candidates = generate_candidates(targets)
    a = score_all(candidates, targets, counters)
    b = score_all(candidates, targets, counters)
    assert a == b


def test_at_least_one_candidate_has_precision_one() -> None:
    """The v3.7 corpus carries enough disambiguating vocabulary
    that at least one candidate hits precision=1.0 on the
    information-theoretic / thermodynamic split."""
    targets = extract_polysemy_targets()
    counters = extract_thermo_counter_set()
    candidates = generate_candidates(targets)
    scores = score_all(candidates, targets, counters)
    assert any(s.info_precision == 1.0 for s in scores)


def test_at_least_one_candidate_meets_coverage_threshold() -> None:
    """Aufgabe 5 — at least one candidate covers >= 30 % of the 15
    polysemy failures (= 5 cases). Without this, no recommendation
    can ever be made."""
    targets = extract_polysemy_targets()
    counters = extract_thermo_counter_set()
    candidates = generate_candidates(targets)
    scores = score_all(candidates, targets, counters)
    assert any(s.coverage >= 0.30 for s in scores)
