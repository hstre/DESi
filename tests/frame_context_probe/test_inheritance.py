"""Aufgaben 4 + 5 — simulator priority and per-layer behaviour."""
from __future__ import annotations

from desi.frame_context_probe.extractor import (
    ContextWindow,
    extract_entropy_targets,
)
from desi.frame_context_probe.inheritance import (
    InheritanceTrace,
    simulate,
    simulate_all,
    simulate_target,
)
from desi.frame_context_probe.signals import ContextSignal
from desi.frames import FrameKind


def test_explicit_frame_in_ctx3_wins() -> None:
    w = ContextWindow(
        ctx_0="Some neutral sentence about a coin.",
        ctx_1="The following question expects a numerical answer.",
        ctx_2="Section: Information Theory — Coding and Bits",
        ctx_3="Frame: thermodynamic",
    )
    r = simulate(w, "explicit-test", FrameKind.THERMODYNAMIC)
    assert r.winning_signal is ContextSignal.EXPLICIT_FRAME
    assert r.inherited_frame is FrameKind.THERMODYNAMIC
    assert r.winning_layer == "ctx_3"


def test_section_header_beats_domain_repetition() -> None:
    # CTX_2 has a clear section header; CTX_1 has domain repetition.
    # Section-header priority > domain-repetition.
    w = ContextWindow(
        ctx_0="A neutral remark.",
        ctx_1="Shannon and bits and coding all matter here.",
        ctx_2="Section: Thermodynamics — Heat and Energy",
        ctx_3="No frame marker here.",
    )
    r = simulate(w, "section-test", FrameKind.THERMODYNAMIC)
    assert r.winning_signal is ContextSignal.SECTION_HEADER
    assert r.inherited_frame is FrameKind.THERMODYNAMIC


def test_domain_repetition_fires_when_no_better_signal() -> None:
    w = ContextWindow(
        ctx_0="Shannon and bits and channel capacity.",
        ctx_1="Nothing relevant here.",
        ctx_2="No section header in this layer.",
        ctx_3="No frame marker either.",
    )
    r = simulate(w, "domain-test", FrameKind.INFORMATION_THEORETIC)
    assert r.winning_signal is ContextSignal.DOMAIN_REPETITION
    assert r.inherited_frame is FrameKind.INFORMATION_THEORETIC


def test_none_when_all_layers_inert() -> None:
    w = ContextWindow(
        ctx_0="A claim with no domain tokens.",
        ctx_1="Another inert sentence.",
        ctx_2="A header without a section keyword.",
        ctx_3="No frame marker.",
    )
    r = simulate(w, "none-test", FrameKind.FRAME_UNDECLARED)
    assert r.winning_signal is ContextSignal.NONE
    assert r.inherited_frame is None
    assert r.winning_layer is None


def test_simulator_emits_one_trace_per_layer() -> None:
    targets = extract_entropy_targets()
    for r in simulate_all(targets):
        layers = [t.layer for t in r.traces]
        assert layers == ["ctx_0", "ctx_1", "ctx_2", "ctx_3"]
        for tr in r.traces:
            assert isinstance(tr, InheritanceTrace)


def test_correct_property_matches_inherited_eq_expected() -> None:
    targets = extract_entropy_targets()
    for r in simulate_all(targets):
        assert r.correct is (r.inherited_frame is r.expected_frame)


def test_real_targets_resolve_via_explicit_marker() -> None:
    # All 4-layer fixtures attach ``Frame: <name>`` in CTX_3, so the
    # simulator must reach perfect accuracy on the rigged windows.
    targets = extract_entropy_targets()
    results = simulate_all(targets)
    assert all(r.correct for r in results)
    # The signal that wins is always EXPLICIT_FRAME for these
    # synthetic windows — that is the whole point of the false-
    # inheritance probe.
    assert all(
        r.winning_signal is ContextSignal.EXPLICIT_FRAME
        for r in results
    )


def test_simulate_target_matches_simulate_window() -> None:
    targets = extract_entropy_targets()
    a = simulate_target(targets[0])
    b = simulate(
        targets[0].context_window,
        targets[0].case_id,
        targets[0].expected_frame,
    )
    assert a.to_dict() == b.to_dict()
