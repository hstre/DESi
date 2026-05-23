"""Tests for v3.7 contamination probe + negative control
(Aufgaben 6 + 7)."""
from __future__ import annotations

from desi.frame_disambiguator_probe import (
    NEGATIVE_CONTROLS,
    excluded_polysemy_texts,
    generate_candidates,
    extract_polysemy_targets,
    probe,
)


def test_ten_negative_controls() -> None:
    """Aufgabe 7 — exactly 10 mixed-frame paraphrases."""
    assert len(NEGATIVE_CONTROLS) == 10


def test_every_negative_control_carries_entropy() -> None:
    for nc in NEGATIVE_CONTROLS:
        assert "entropy" in nc.text.lower()


def test_no_negative_control_is_information_theoretic() -> None:
    from desi.frames import FrameKind
    for nc in NEGATIVE_CONTROLS:
        assert nc.expected_frame is not FrameKind.INFORMATION_THEORETIC


def test_probe_returns_unit_interval_risk() -> None:
    targets = extract_polysemy_targets()
    candidates = generate_candidates(targets)
    exclude = excluded_polysemy_texts()
    for c in candidates[:20]:
        r = probe(c, excluded_case_ids=exclude)
        assert 0.0 <= r.contamination_risk <= 1.0


def test_probe_is_deterministic() -> None:
    targets = extract_polysemy_targets()
    candidates = generate_candidates(targets)
    exclude = excluded_polysemy_texts()
    c0 = candidates[0]
    a = probe(c0, excluded_case_ids=exclude)
    b = probe(c0, excluded_case_ids=exclude)
    assert a == b


def test_excluded_polysemy_texts_match_target_count() -> None:
    targets = extract_polysemy_targets()
    excluded = excluded_polysemy_texts()
    assert len(excluded) == len(targets)
