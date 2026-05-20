"""Aufgabe 1 — target extraction from v3.9 artifacts."""
from __future__ import annotations

from desi.frame_tension_audit.extractor import (
    TensionTarget,
    extract_tension_targets,
)


_REQUIRED_FIELDS = (
    "case_id",
    "text",
    "outer_frame",
    "inner_frame",
    "ground_truth_relation",
    "consistency_score",
    "source_group",
    "source_benchmark",
)


def test_targets_extracted() -> None:
    # Aufgabe 1 fail-closed: zero TENSION cases means nothing to
    # audit; the extractor must raise instead.
    targets = extract_tension_targets()
    assert len(targets) > 0


def test_required_fields_present_on_each_target() -> None:
    targets = extract_tension_targets()
    for t in targets:
        assert isinstance(t, TensionTarget)
        d = t.to_dict()
        for key in _REQUIRED_FIELDS:
            assert key in d, f"{t.case_id} missing field {key}"


def test_targets_are_unique_by_case_id() -> None:
    targets = extract_tension_targets()
    ids = [t.case_id for t in targets]
    assert len(ids) == len(set(ids))


def test_extraction_is_deterministic() -> None:
    a = [t.to_dict() for t in extract_tension_targets()]
    b = [t.to_dict() for t in extract_tension_targets()]
    assert a == b


def test_targets_include_both_corpus_and_manipulation_sources() -> None:
    sources = {t.source_group for t in extract_tension_targets()}
    assert sources == {"corpus_outcomes", "manipulation_outcomes"}


def test_all_targets_are_tension() -> None:
    for t in extract_tension_targets():
        # The extractor pulls only TENSION cases — every recorded
        # ground_truth_relation must be exactly "frame_tension"
        # (those came from v3.9 GROUP_B and the manipulation set).
        assert t.ground_truth_relation == "frame_tension", t.case_id
