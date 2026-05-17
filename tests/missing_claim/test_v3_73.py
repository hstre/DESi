"""v3.73 — known-claim removal tests."""
from __future__ import annotations

import json
import pathlib

from desi.missing_claim.remove import (
    ClaimRole, PROBE_RADIUS, TEST_CLAIM_SET,
    all_removal_outcomes,
)
from desi.missing_claim.report import (
    build_removal_perturbation_artifact,
    build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_claim_roles_match_directive() -> None:
    expected = {
        "high_coverage", "low_coverage",
        "bridge", "redundant",
    }
    assert {r.value for r in ClaimRole} == expected


def test_test_claim_set_one_per_role() -> None:
    roles = [role for _, role in TEST_CLAIM_SET]
    assert set(roles) == {
        "high_coverage", "low_coverage",
        "bridge", "redundant",
    }
    assert len(roles) == len(set(roles))


def test_all_removal_outcomes_count() -> None:
    assert len(all_removal_outcomes()) == 4


def test_high_coverage_removal_zero_in_this_corpus() -> None:
    """High coverage anchor's coverage is duplicated
    by REDUNDANT; removing it loses 0 coverage."""
    outs = {
        o.role: o for o in all_removal_outcomes()
    }
    assert outs["high_coverage"].coverage_loss == 0


def test_low_coverage_removal_zero() -> None:
    outs = {
        o.role: o for o in all_removal_outcomes()
    }
    assert outs["low_coverage"].coverage_loss == 0
    assert outs[
        "low_coverage"
    ].perturbation_magnitude == 0.0


def test_bridge_removal_loses_twelve() -> None:
    """The BRIDGE anchor in the test set is the only
    12-coverage anchor; removing it loses 12
    leakages."""
    outs = {
        o.role: o for o in all_removal_outcomes()
    }
    assert outs["bridge"].coverage_loss == 12


def test_bridge_perturbation_largest() -> None:
    """BRIDGE produces the largest perturbation
    magnitude in this corpus, not HIGH (because HIGH
    is duplicated by REDUNDANT)."""
    outs = all_removal_outcomes()
    by_role = {
        o.role: o.perturbation_magnitude for o in outs
    }
    assert by_role["bridge"] > by_role["high_coverage"]
    assert by_role["bridge"] > by_role["redundant"]


def test_redundant_removal_zero_coverage_loss() -> None:
    """REDUNDANT's coverage is replicated by HIGH;
    removing it loses 0."""
    outs = {
        o.role: o for o in all_removal_outcomes()
    }
    assert outs["redundant"].coverage_loss == 0


def test_redundant_removal_shifts_identities() -> None:
    """Even with 0 coverage loss, removing REDUNDANT
    changes the nearest-anchor identity for the
    leakages it covered (they now look at HIGH
    instead)."""
    outs = {
        o.role: o for o in all_removal_outcomes()
    }
    assert outs["redundant"].affected_trajectories > 0


def test_stop_rule_high_le_redundant_triggers() -> None:
    """Empirical: high (0.0) <= redundant (13.37);
    the directive's stop rule triggers in this
    corpus. Hypothesis weak (documented, not
    halted)."""
    r = build_report()
    assert r.hypothesis_weak is True
    assert r.high_vs_redundant_ordering == (
        "high_below_redundant"
    )


def test_total_support_shift_positive() -> None:
    """At least the bridge-loss leakages shift their
    fire status."""
    r = build_report()
    assert r.total_support_shift > 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_weak() -> None:
    assert build_report().recommendation == (
        "PERTURBATION_HYPOTHESIS_WEAK"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PERTURBATION_HYPOTHESIS_HOLDS",
        "PERTURBATION_HYPOTHESIS_WEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_outcomes() -> None:
    art = build_removal_perturbation_artifact()
    assert len(art["removal_outcomes"]) == 4
    assert len(art["test_claim_set"]) == 4


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_73" / "report.json").read_text(
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
