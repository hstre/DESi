"""Aufgaben 3 + 4 + 6 + 7 — runner, metrics, failure classes, pressure."""
from __future__ import annotations

from desi.causal_redteam import (
    ALL_ADVERSARIAL_CASES,
    AdversarialFailureClass,
    compute_metrics,
    compute_pressure_map,
    run_attacks,
)


def test_runner_returns_one_outcome_per_case() -> None:
    outs = run_attacks()
    assert len(outs) == len(ALL_ADVERSARIAL_CASES)


def test_runner_is_deterministic() -> None:
    a = [o.to_dict() for o in run_attacks()]
    b = [o.to_dict() for o in run_attacks()]
    assert a == b


def test_failure_class_enum_has_ten_values() -> None:
    assert len(list(AdversarialFailureClass)) == 10
    assert {f.value for f in AdversarialFailureClass} == {
        "negation_bypass",
        "quantifier_bypass",
        "authority_bypass",
        "metaphor_bypass",
        "frame_switch_bypass",
        "tool_contamination",
        "cycle_bypass",
        "semantic_leap",
        "multi_vector_combination",
        "unknown",
    }


def test_every_successful_attack_carries_failure_class() -> None:
    for o in run_attacks():
        if o.attack_succeeded:
            assert o.failure_class is not None, o.case_id
        else:
            assert o.failure_class is None, o.case_id


def test_metrics_self_consistent() -> None:
    outs = run_attacks()
    m = compute_metrics(outs)
    assert m.total == len(outs)
    assert m.attack_success_count + sum(
        1 for o in outs if not o.attack_succeeded
    ) == m.total
    # By construction false_support == attack_success.
    assert m.false_support_count == m.attack_success_count


def test_pressure_map_partitions_corpus() -> None:
    outs = run_attacks()
    p = compute_pressure_map(outs)
    # Every case is either "clean" (no marker present) or has at
    # least one marker. The sum doesn't have to equal the total
    # because multiple markers can co-occur, but clean_cases plus
    # any-marker counts must cover the corpus.
    activated = sum(
        1 for o in outs if any(o.pressure_markers.values())
    )
    assert p.clean_cases + activated == len(outs)


def test_recommendation_is_none_when_attacks_succeed() -> None:
    from datetime import datetime, timezone
    from desi.causal_redteam import build_redteam_report
    r = build_redteam_report(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    if r.metrics.attack_success_count > 0:
        assert r.recommended_next == "NONE"
        assert "attack_success_count" in r.recommendation_reason
