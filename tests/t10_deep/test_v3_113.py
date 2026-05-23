"""v3.113 - structural topology census tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_deep.graph import (
    all_structural_outcomes,
    signal_candidates,
    top_candidate,
)
from desi.t10_deep.report import (
    AUC_SIGNAL_THRESHOLD,
    build_report,
    build_t10_structural_topology_artifact,
)
from desi.t10_deep.topology import (
    STRUCTURAL_CANDIDATES,
    StructuralCandidate,
    structural_value,
)


def test_twelve_structural_candidates() -> None:
    """Closed enum: 12 structural features."""
    assert len(STRUCTURAL_CANDIDATES) == 12


def test_candidate_enum_matches_taxonomy() -> None:
    vals = {
        c.value for c in StructuralCandidate
    }
    assert vals == set(STRUCTURAL_CANDIDATES)


def test_structural_value_deterministic() -> None:
    a = structural_value(
        "inference_depth", "v314:A01",
    )
    b = structural_value(
        "inference_depth", "v314:A01",
    )
    assert a == b


def test_inference_depth_is_state_count() -> None:
    """Trajectories all have 5 states."""
    assert structural_value(
        "inference_depth", "v314:A01",
    ) == 5.0


def test_all_candidates_have_outcomes() -> None:
    outs = all_structural_outcomes()
    assert len(outs) == 12


def test_every_candidate_has_zero_variance() -> None:
    """Killerfrage answer: welche echte
    strukturelle Information fehlt DESi? -
    ALLES. Every structural candidate evaluates
    to the SAME value across every entangled
    anchor."""
    for o in all_structural_outcomes():
        assert o.variance_on_entangled_pool == 0.0


def test_every_candidate_auc_at_chance() -> None:
    for o in all_structural_outcomes():
        assert o.mean_auc == 0.5


def test_signal_candidates_empty() -> None:
    """No candidate exceeds the 0.55 signal
    threshold."""
    assert signal_candidates() == ()


def test_top_candidate_auc_below_gate() -> None:
    """Concept Gate condition #1:
    top_candidate_auc >= 0.70. FAILS."""
    assert top_candidate().mean_auc < (
        AUC_SIGNAL_THRESHOLD
    )


def test_top_candidate_margin_is_zero() -> None:
    assert top_candidate().mean_margin == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRUCTURAL_SIGNAL_FOUND",
        "STRUCTURAL_SIGNAL_WEAK",
        "NO_STRUCTURAL_SIGNAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_no_signal() -> None:
    assert build_report().recommendation == (
        "NO_STRUCTURAL_SIGNAL"
    )


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_structural_topology_artifact()
    assert len(art["structural_outcomes"]) == 12


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_113" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
