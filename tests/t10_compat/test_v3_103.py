"""v3.103 - T10 historical compatibility tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_compat.compatibility import (
    CONTRADICTION_TYPE,
    augmented_dict,
    contradiction_type_for,
    contradiction_type_for_text,
)
from desi.t10_compat.replay import (
    all_historical_gate_outcomes,
    beneficial_flip_count,
    compatibility_score,
    failure_class_delta,
    gate_flip_count,
    historical_auc_delta,
    replay_hash_breakage,
)
from desi.t10_compat.report import (
    HISTORICAL_AUC_DELTA_TOLERANCE,
    build_report,
    build_t10_historical_compatibility_artifact,
)


def test_contradiction_type_for_circular_text() -> None:
    """The selected candidate fires on the G
    family's circular pattern."""
    text = (
        "The argument rests on the lemma. "
        "The lemma rests on the argument."
    )
    assert (
        contradiction_type_for_text(text) == 1.0
    )


def test_contradiction_type_for_syllogism() -> None:
    """It does NOT fire on E's syllogistic
    pattern."""
    text = (
        "All ravens are black. "
        "This bird is a raven. "
        "Therefore this bird is black."
    )
    assert (
        contradiction_type_for_text(text) == 0.0
    )


def test_contradiction_type_for_unknown_id() -> None:
    """Unknown trajectory ids return 0.0 - no
    contradiction signal by construction."""
    assert (
        contradiction_type_for("nonexistent")
        == 0.0
    )


def test_augmented_dict_appends_one_coord() -> None:
    base = {"a": (0.0, 1.0, 2.0)}
    out = augmented_dict(base)
    assert len(out["a"]) == 4


def test_gate_flip_count_is_zero() -> None:
    """Concept Gate condition #4: no adverse
    flips. The +1 dim only IMPROVES gate
    outcomes; no historical pass becomes a
    fail."""
    assert gate_flip_count() == 0


def test_beneficial_flips_present() -> None:
    """The whole point of T10 is to flip the
    entangled-pair gates from FAIL to PASS."""
    assert beneficial_flip_count() > 0


def test_replay_hash_breakage_is_zero() -> None:
    """Artifacts on disk are frozen; T10 is a
    counterfactual injection, not a code
    change."""
    assert replay_hash_breakage() == 0


def test_failure_class_delta_is_zero() -> None:
    """Failure class is derived from state_vector
    semantics; the +1 dim does not change
    state-derived classification."""
    assert failure_class_delta() == 0


def test_compatibility_score_is_one() -> None:
    """Every historical gate is either unchanged
    or flips beneficially."""
    assert compatibility_score() == 1.0


def test_plateau_invariant_sprints_unchanged() -> None:
    """Mozart, missing_claim, redundancy_classes,
    doppelgaenger, minimal_features all read
    plateau anchors only; the +1 dim is a
    constant 0 for plateau anchors so the
    counterfactual must equal the stored
    value."""
    for o in all_historical_gate_outcomes():
        plateau_sprints = {
            "v3.69 mozart_probe",
            "v3.73 missing_claim",
            "v3.79 redundancy_classes",
            "v3.81 doppelgaenger",
            "v3.82 minimal_features",
        }
        if o.sprint_id in plateau_sprints:
            assert (
                o.counterfactual_value
                == o.stored_value
            )


def test_entangled_pair_gates_flip_beneficially() -> None:
    """The v3.94, v3.96, v3.100 gates are the
    ones T10 was designed to rescue."""
    rescued = [
        "v3.94 entangled_ablation",
        "v3.96 entangled_resolution",
        "v3.100 compression_audit",
    ]
    outs = all_historical_gate_outcomes()
    for sid in rescued:
        relevant = [
            o for o in outs if o.sprint_id == sid
        ]
        assert relevant, sid
        for o in relevant:
            assert o.flip == "beneficial_flip"


def test_historical_auc_delta_in_unit_interval() -> None:
    assert 0.0 <= historical_auc_delta() <= 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "HISTORICAL_COMPATIBLE",
        "HISTORICAL_COMPATIBLE_AUC_DRIFT",
        "HISTORICAL_INCOMPATIBLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_acknowledges_auc_drift() -> None:
    """Adverse flips are zero but the entangled-
    pair AUCs jump from sub-threshold to 1.0;
    the verdict label must reflect that the
    delta exceeds 0.05."""
    r = build_report()
    if r.historical_auc_delta > (
        HISTORICAL_AUC_DELTA_TOLERANCE
    ):
        assert r.recommendation == (
            "HISTORICAL_COMPATIBLE_AUC_DRIFT"
        )


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_historical_compatibility_artifact()
    assert len(art["historical_gate_outcomes"]) >= 10


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_103" / "report.json").read_text(
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
