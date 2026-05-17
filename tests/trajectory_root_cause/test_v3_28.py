"""v3.28 — root-cause observer tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.trajectory_control.negative_controls import (
    all_ncs,
)
from desi.trajectory_root_cause.cause import (
    CauseClass, all_known,
)
from desi.trajectory_root_cause.classifier import (
    classify_all, classify_trajectory,
)
from desi.trajectory_root_cause.report import (
    MAX_CAUSE_NC_FP_RATE, MAX_UNKNOWN_RATE,
    MIN_REPLAY_STABILITY,
    build_distribution_artifact, build_report,
    build_taxonomy_artifact,
)
from desi.trajectory_root_cause.signals import (
    compute_signals,
)


def test_cause_class_is_closed_set() -> None:
    expected = {
        "SUPPORT_DECAY", "FRAME_COLLISION",
        "BRANCH_OVERLOAD", "CAUSAL_LEAP",
        "CONFIDENCE_OSCILLATION", "UNKNOWN",
    }
    assert {c.value for c in CauseClass} == expected


def test_unknown_is_first_class_member() -> None:
    """Directive: UNKNOWN must be possible. No forced
    classification."""
    assert "UNKNOWN" in {c.value for c in CauseClass}
    assert CauseClass.UNKNOWN.value not in all_known()


def test_all_cliffs_classified_or_unknown() -> None:
    """Directive: keine Freitexte. Every assignment is
    one of the closed classes."""
    assignments = classify_all(extract_all_trajectories())
    allowed = {c.value for c in CauseClass}
    for a in assignments:
        assert a.primary_cause in allowed, a.trajectory_id


def test_unknown_rate_meets_gate() -> None:
    r = build_report()
    assert r.unknown_rate <= MAX_UNKNOWN_RATE


def test_cause_nc_fp_rate_meets_stop_rule() -> None:
    """Directive Stop Rule: cause_nc_fp > 0.10 halts."""
    r = build_report()
    assert r.cause_nc_fp_rate <= MAX_CAUSE_NC_FP_RATE
    assert not r.halt


def test_replay_stability_is_one() -> None:
    r = build_report()
    assert r.replay_stability >= MIN_REPLAY_STABILITY


def test_no_nc_gets_a_named_cause() -> None:
    """Each of the four NC kinds must classify as
    UNKNOWN. NCs have no real cliff and the classifier
    must not produce a cause assignment."""
    for nc in all_ncs():
        a = classify_trajectory(nc.trajectory)
        assert a.primary_cause == CauseClass.UNKNOWN.value, (
            nc.nc_id, a.primary_cause,
        )


def test_classifier_deterministic_across_calls() -> None:
    trajs = extract_all_trajectories()[:20]
    a1 = classify_all(trajs)
    a2 = classify_all(trajs)
    for x, y in zip(a1, a2):
        assert x.primary_cause == y.primary_cause
        assert x.secondary_causes == y.secondary_causes


def test_artifact_taxonomy_matches_taxonomy_module() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_28"
         / "root_cause_taxonomy.json").read_text(
            encoding="utf-8",
        )
    )
    classes = {c["name"] for c in art["classes"]}
    assert classes == {c.value for c in CauseClass}


def test_artifact_distribution_covers_all_cliffs() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_28"
         / "cliff_cause_distribution.json").read_text(
            encoding="utf-8",
        )
    )
    assigns = art["assignments"]
    rep = build_report()
    assert len(assigns) == rep.cliff_count


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_28" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    assert art == live


def test_multi_cause_rate_in_unit_interval() -> None:
    r = build_report()
    assert 0.0 <= r.multi_cause_rate <= 1.0


def test_recommendation_is_observer_ready() -> None:
    """Empirical: with the tuned thresholds the v3.28
    gate is satisfied on the current corpus."""
    assert build_report().recommendation == (
        "ROOT_CAUSE_OBSERVER_READY"
    )
