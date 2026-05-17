"""v3.37 — Self-Explanation Audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.plateau_cross_transfer.transfer import (
    collect_universe,
)
from desi.self_explanation.attribution import (
    confidence_hold_was_noop, decisive_dimension,
    first_changed_dimension,
)
from desi.self_explanation.counterfactual import (
    per_dimension_deltas, strategy_b_counterfactual,
)
from desi.self_explanation.explainer import (
    PLATEAU_PRIMARY_CAUSE, explain_all_movers,
    explain_one, explain_unexpected_rescues,
)
from desi.self_explanation.report import (
    EXPECTED_RESCUE_COUNT, MAX_UNEXPLAINED_CASES,
    build_overgeneralized_claims_artifact, build_report,
    build_self_explanation_artifact,
)


def _trajs():
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def test_plateau_cause_anchor_matches_directive() -> None:
    """Plateau primary cause (from v3.32) is the anchor
    for the 'identical_to_plateau_cause' check."""
    assert PLATEAU_PRIMARY_CAUSE == "CONFIDENCE_OSCILLATION"


def test_strategy_b_counterfactual_length_preserved() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    cf = strategy_b_counterfactual(t.states)
    assert len(cf) == len(t.states)


def test_per_dimension_deltas_empty_on_identity() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    assert per_dimension_deltas(t.states, t.states) == ()


def test_first_changed_dimension_handles_empty() -> None:
    assert first_changed_dimension(()) is None


def test_decisive_dimension_handles_no_change() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    assert decisive_dimension(
        t.states, t.states, (),
    ) is None


def test_confidence_hold_noop_holds_for_all_rescues() -> None:
    """In this corpus the confidence_hold component
    moves no confidence value at any state."""
    for e in explain_unexpected_rescues():
        assert e.confidence_hold_noop is True


def test_unexpected_rescues_count_is_14() -> None:
    """v3.35 finding pinned: 14 false_rescue
    trajectories (all CAUSAL_LEAP)."""
    assert len(explain_unexpected_rescues()) == EXPECTED_RESCUE_COUNT


def test_decisive_dimension_is_support_state() -> None:
    """The audit-step withdrawal is the only thing
    moving the verdict, so support_state is always
    decisive on the rescue cohort."""
    for e in explain_unexpected_rescues():
        assert e.decisive_dimension == "support_state"


def test_no_unexpected_rescue_shares_plateau_cause() -> None:
    """All 14 unexpected rescues come from CAUSAL_LEAP;
    none share CONFIDENCE_OSCILLATION (the plateau
    cause). This is the structural finding."""
    for e in explain_unexpected_rescues():
        assert e.identical_to_plateau_cause is False
        assert e.original_primary_cause == "CAUSAL_LEAP"


def test_machine_readable_reason_is_closed() -> None:
    allowed = {
        "AUDIT_WITHDRAW_ON_PLATEAU_CAUSE",
        "AUDIT_WITHDRAW_ON_FOREIGN_CAUSE",
        "AUDIT_WITHDRAW_WITH_CONFIDENCE_LIFT",
        "NO_VERDICT_CHANGE",
    }
    for e in explain_all_movers():
        assert (
            e.machine_readable_reason in allowed
            or e.machine_readable_reason.startswith(
                "DECISIVE_",
            )
        )


def test_unexpected_rescue_reason_is_foreign_cause() -> None:
    for e in explain_unexpected_rescues():
        assert e.machine_readable_reason == (
            "AUDIT_WITHDRAW_ON_FOREIGN_CAUSE"
        )


def test_self_explained_count_matches_expected() -> None:
    """Paper-10 v3 gate #1: self_explained_count = 14."""
    assert build_report().self_explained_count == (
        EXPECTED_RESCUE_COUNT
    )


def test_unexplained_cases_meets_gate() -> None:
    """Paper-10 v3 gate #2: unexplained_cases = 0."""
    assert build_report().unexplained_cases == (
        MAX_UNEXPLAINED_CASES
    )


def test_explanation_replay_stability_is_one() -> None:
    assert build_report().explanation_replay_stability == 1.0


def test_explain_one_round_trip() -> None:
    trajs = _trajs()
    movers = explain_all_movers()
    a = movers[0]
    b = explain_one(trajs[a.trajectory_id])
    assert a.to_dict() == b.to_dict()


def test_plateau_movers_count_is_twenty() -> None:
    assert build_report().plateau_mover_count == 20


def test_overgeneralized_claims_count_is_fourteen() -> None:
    """One overgeneralized-stabilization claim per
    unexpected rescue."""
    art = build_overgeneralized_claims_artifact()
    assert art["claim_count"] == 14


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SELF_EXPLANATION_COMPLETE",
        "HALT_UNEXPLAINED_CASES",
        "HALT_EXPLAIN_COUNT_MISMATCH",
    }
    assert build_report().recommendation in allowed


def test_self_explanation_artifact_records_movers() -> None:
    art = build_self_explanation_artifact()
    assert len(art["explanations"]) == 20 + 14  # 20 plateau + 14 rescue


def test_dominant_dimensions_are_support_state() -> None:
    r = build_report()
    assert r.dominant_changed_dimension == "support_state"
    assert r.dominant_decisive_dimension == "support_state"


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_37" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    # rationale carries dict-iteration ordering of
    # reason_distribution; compare stable fields only.
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
