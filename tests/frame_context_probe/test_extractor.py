"""Aufgaben 1 + 2 — entropy targets + context-window assembly."""
from __future__ import annotations

from desi.frame_context_probe.extractor import (
    ContextWindow,
    TargetCase,
    extract_entropy_targets,
)
from desi.frames import FrameKind


def test_target_count_meets_minimum() -> None:
    # Aufgabe 1: at least 25 entropy-bearing targets across v3.4–v3.6.
    targets = extract_entropy_targets()
    assert len(targets) >= 25


def test_targets_are_unique_by_case_id() -> None:
    targets = extract_entropy_targets()
    ids = [t.case_id for t in targets]
    assert len(ids) == len(set(ids))


def test_every_target_mentions_entropy() -> None:
    targets = extract_entropy_targets()
    assert targets, "expected non-empty target set"
    for t in targets:
        assert "entropy" in t.text.lower(), t.case_id


def test_every_target_has_context_window() -> None:
    targets = extract_entropy_targets()
    for t in targets:
        assert isinstance(t.context_window, ContextWindow)
        layers = t.context_window.all_layers()
        assert len(layers) == 4
        # Each layer is a non-empty string.
        for layer in layers:
            assert isinstance(layer, str) and layer.strip()


def test_context_layer_zero_equals_text() -> None:
    # CTX_0 must always be the case sentence verbatim.
    targets = extract_entropy_targets()
    for t in targets:
        assert t.context_window.ctx_0 == t.text


def test_source_benchmarks_cover_v34_v35_v36() -> None:
    targets = extract_entropy_targets()
    sources = {t.source_benchmark for t in targets}
    assert "v3.4 frame benchmark" in sources
    assert "v3.5 invariance" in sources
    assert "v3.6 failure-audit NC" in sources


def test_to_dict_round_trip_shape() -> None:
    targets = extract_entropy_targets()
    sample = targets[0].to_dict()
    assert set(sample) == {
        "case_id", "text", "expected_frame", "detected_frame",
        "source_benchmark", "context_window",
    }
    cw = sample["context_window"]
    assert set(cw) == {"ctx_0", "ctx_1", "ctx_2", "ctx_3"}


def test_window_frame_specific_fixtures_disjoint() -> None:
    # Spot-check: a thermo target must get a thermo header / frame.
    targets = extract_entropy_targets()
    thermo = [
        t for t in targets if t.expected_frame is FrameKind.THERMODYNAMIC
    ]
    assert thermo, "v3.4 FA_01 should appear as thermodynamic target"
    for t in thermo:
        assert "Thermodynamics" in t.context_window.ctx_2
        assert t.context_window.ctx_3 == "Frame: thermodynamic"
