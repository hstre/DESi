"""v3.77 — negative controls tests."""
from __future__ import annotations

import json
import pathlib

from desi.missing_negative_controls.negative_controls import (
    false_missing_claim_rate,
    noise_rejection_rate, null_stability,
)
from desi.missing_negative_controls.null_space import (
    NullControlKind,
    all_null_control_outcomes,
    perturb_vector, run_one_null_control,
)
from desi.missing_negative_controls.report import (
    NEPTUN_FALSE_MISSING_CEILING,
    build_missing_claim_negative_controls_artifact,
    build_report,
)


def test_null_control_kinds_match_directive() -> None:
    expected = {
        "random_jitter", "frame_drift",
        "branch_variation", "noise_only",
    }
    assert {k.value for k in NullControlKind} == expected


def test_neptun_false_missing_ceiling() -> None:
    assert NEPTUN_FALSE_MISSING_CEILING == 0.20


def test_all_outcomes_count() -> None:
    assert len(all_null_control_outcomes()) == 4


def test_each_null_kind_has_outcome() -> None:
    outs = {
        o.kind: o for o in all_null_control_outcomes()
    }
    for k in NullControlKind:
        assert k.value in outs


def test_baseline_coverage_consistent() -> None:
    """All four perturbations start from the same
    133-leakage baseline."""
    for o in all_null_control_outcomes():
        assert o.baseline_coverage_size == 133


def test_all_null_controls_reject_noise() -> None:
    """All 4 null controls correctly produce 0
    false missing claims at their tuned budgets."""
    for o in all_null_control_outcomes():
        assert o.false_missing_claims == 0


def test_false_missing_claim_rate_meets_gate() -> None:
    """Neptun concept gate #5:
    false_missing_claim_rate <= 0.20."""
    rate = false_missing_claim_rate(
        all_null_control_outcomes(),
    )
    assert rate <= NEPTUN_FALSE_MISSING_CEILING


def test_false_missing_claim_rate_is_zero() -> None:
    rate = false_missing_claim_rate(
        all_null_control_outcomes(),
    )
    assert rate == 0.0


def test_noise_rejection_rate_is_one() -> None:
    rate = noise_rejection_rate(
        all_null_control_outcomes(),
    )
    assert rate == 1.0


def test_null_stability_is_one() -> None:
    assert null_stability() == 1.0


def test_run_one_null_control_returns_outcome() -> None:
    for k in NullControlKind:
        o = run_one_null_control(k.value)
        assert o.kind == k.value
        assert o.perturbed_anchor_count == 4


def test_perturb_vector_deterministic() -> None:
    """Two calls with same anchor_id / kind / vector
    return the same perturbation."""
    v = (1.0,) * 45
    a = perturb_vector("test", v, "noise_only")
    b = perturb_vector("test", v, "noise_only")
    assert a == b


def test_perturb_vector_no_op_for_unknown_kind() -> None:
    v = (1.0,) * 45
    assert perturb_vector("test", v, "unknown") == v


def test_frame_drift_only_changes_frame_dim() -> None:
    """FRAME_DRIFT touches only frame_id components
    (dim 0 of each state)."""
    v = (1.0,) * 45
    out = perturb_vector("test", v, "frame_drift")
    for i in range(45):
        if i % 9 == 0:  # frame_id dim of each state
            # might change; not required for ALL
            # since deterministic noise can be 0
            pass
        else:
            assert out[i] == v[i]


def test_branch_variation_only_changes_branch_dim() -> None:
    """BRANCH_VARIATION touches only branch_cost
    components (dim 6 of each state)."""
    v = (1.0,) * 45
    out = perturb_vector(
        "test", v, "branch_variation",
    )
    for i in range(45):
        if i % 9 == 6:  # branch_cost dim of each state
            pass
        else:
            assert out[i] == v[i]


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_passes() -> None:
    assert build_report().recommendation == (
        "NULL_CONTROL_PASSES"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NULL_CONTROL_PASSES", "NULL_CONTROL_FAILS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_outcomes() -> None:
    art = build_missing_claim_negative_controls_artifact()
    assert len(art["null_outcomes"]) == 4
    assert len(art["null_kinds"]) == 4


def test_neptun_concept_gate_summary() -> None:
    """All six Neptun concept gates evaluated end-to-
    end. Gate #1 is the empirical FAILURE."""
    from desi.missing_blind.report import (
        build_report as v376,
    )
    from desi.missing_candidate.report import (
        build_report as v375,
    )
    from desi.missing_claim.report import (
        build_report as v373,
    )
    from desi.missing_localization.report import (
        build_report as v374,
    )
    r73 = v373()
    r74 = v374()
    r75 = v375()
    r76 = v376()
    r77 = build_report()
    # Gate 1: high > redundant (FAILS empirically)
    assert r73.hypothesis_weak is True
    # Gate 2: localization_accuracy >= 0.70
    assert r74.localization_accuracy >= 0.70
    # Gate 3: candidate_match_score >= 0.70
    assert r75.candidate_match_score >= 0.70
    # Gate 4: region_recall >= 0.70
    assert r76.region_recall >= 0.70
    # Gate 5: false_missing_claim_rate <= 0.20
    assert r77.false_missing_claim_rate <= 0.20
    # Gate 6: replay stability across all sprints
    assert r73.replay_stability == 1.0
    assert r74.replay_stability == 1.0
    assert r75.replay_stability == 1.0
    assert r76.replay_stability == 1.0
    assert r77.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_77" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
