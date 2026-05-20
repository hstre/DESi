"""Aufgabe 4 + 5 + 7 — agreement metrics deterministic and
convergence correctly detected."""
from __future__ import annotations

import statistics

from ._helpers import load_agreement, load_results


def test_total_reviewers_matches_results() -> None:
    a = load_agreement()
    r = load_results()
    assert a["total_reviewers"] == len(r["reviewers"])


def test_hash_agreement_rate_in_unit_interval() -> None:
    a = load_agreement()
    assert 0.0 <= a["hash_agreement_rate"] <= 1.0


def test_replay_agreement_rate_in_unit_interval() -> None:
    a = load_agreement()
    assert 0.0 <= a["replay_agreement_rate"] <= 1.0


def test_mean_falsifiability_recomputes_from_results() -> None:
    a = load_agreement()
    r = load_results()
    scores = [rev["falsifiability_score"] for rev in r["reviewers"]]
    expected = round(statistics.mean(scores), 6)
    assert a["mean_falsifiability"] == expected


def test_std_falsifiability_recomputes_from_results() -> None:
    a = load_agreement()
    r = load_results()
    scores = [rev["falsifiability_score"] for rev in r["reviewers"]]
    expected = round(statistics.pstdev(scores), 6)
    assert a["std_falsifiability"] == expected


def test_hash_agreement_rate_recomputes_from_results() -> None:
    a = load_agreement()
    r = load_results()
    expected = round(
        sum(1 for x in r["reviewers"] if x["hash_verified"])
        / len(r["reviewers"]), 6,
    )
    assert a["hash_agreement_rate"] == expected


def test_replay_agreement_rate_recomputes_from_results() -> None:
    a = load_agreement()
    r = load_results()
    expected = round(
        sum(1 for x in r["reviewers"] if x["replay_verified"])
        / len(r["reviewers"]), 6,
    )
    assert a["replay_agreement_rate"] == expected


def test_cross_model_convergence_true_when_any_shared() -> None:
    """Aufgabe 5: convergence iff >= 2 reviewers share a hidden
    assumption or contamination risk."""
    a = load_agreement()
    expected = bool(
        a["shared_hidden_assumptions"] or a["shared_contamination_risks"]
    )
    assert a["cross_model_convergence"] is expected


def test_every_shared_finding_has_at_least_two_reviewers() -> None:
    a = load_agreement()
    for s in a["shared_hidden_assumptions"]:
        assert len(set(s["reviewers"])) >= 2
    for s in a["shared_contamination_risks"]:
        assert len(set(s["reviewers"])) >= 2


def test_convergence_fact_check_at_least_one_shared_finding() -> None:
    """The v3.3 run must produce at least one cross-model
    convergence point so the metric has signal."""
    a = load_agreement()
    total_shared = (
        len(a["shared_hidden_assumptions"])
        + len(a["shared_contamination_risks"])
    )
    assert total_shared >= 1, (
        "no cross-model convergence — agreement metric carries no signal"
    )
