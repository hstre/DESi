"""v3.122 - regression governance tests."""
from __future__ import annotations

import json
import pathlib

from desi.regression_governance.governance import (
    MUTATION_KINDS,
    MutationKind,
    all_classified_commits,
)
from desi.regression_governance.policy import (
    RegressionPolicy,
    avoidable_full_runs,
    commit_classification_counts,
    core_or_gate_commit_count,
    historical_risk_level,
    recommended_policy_for,
    wasted_cpu_hours,
)
from desi.regression_governance.report import (
    build_regression_governance_artifact,
    build_report,
)


def test_four_mutation_kinds() -> None:
    assert len(MUTATION_KINDS) == 4


def test_three_regression_policies() -> None:
    assert len({p.value for p in RegressionPolicy}) == 3


def test_classification_counts_sum_to_commits() -> None:
    counts = commit_classification_counts()
    assert sum(counts.values()) == len(
        all_classified_commits(),
    )


def test_core_path_maps_to_full_regression() -> None:
    assert recommended_policy_for(
        MutationKind.CORE_MUTATION.value,
    ) == RegressionPolicy.FULL_REGRESSION.value


def test_docs_only_maps_to_no_regression() -> None:
    assert recommended_policy_for(
        MutationKind.DOCS_ONLY.value,
    ) == RegressionPolicy.NO_REGRESSION.value


def test_analysis_only_maps_to_targeted_replay() -> None:
    assert recommended_policy_for(
        MutationKind.ANALYSIS_ONLY.value,
    ) == (
        RegressionPolicy.TARGETED_REPLAY.value
    )


def test_avoidable_full_runs_positive() -> None:
    """Killerfrage: verbrennen wir gerade
    Wissenschaftszeit? JA - many past
    analysis-only commits triggered a full
    regression."""
    assert avoidable_full_runs() > 0


def test_wasted_cpu_hours_positive() -> None:
    assert wasted_cpu_hours() > 0.0


def test_historical_risk_in_closed_set() -> None:
    allowed = {"low", "moderate", "high"}
    assert historical_risk_level() in allowed


def test_historical_risk_is_low() -> None:
    """The historical core-mutation count is
    small enough to call the policy switch
    safe."""
    assert historical_risk_level() == "low"


def test_core_or_gate_commit_count_minimal() -> None:
    """The closed core-path list is
    conservative: only a handful of commits
    should qualify as CORE_MUTATION."""
    assert core_or_gate_commit_count() <= 10


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "POLICY_ALREADY_OPTIMAL",
        "POLICY_RECOMMENDED",
        "POLICY_RISKY",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_recommended() -> None:
    assert build_report().recommendation == (
        "POLICY_RECOMMENDED"
    )


def test_artifact_has_classifications() -> None:
    art = build_regression_governance_artifact()
    assert len(art["classified_commits"]) == (
        len(all_classified_commits())
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_122" / "report.json").read_text(
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
