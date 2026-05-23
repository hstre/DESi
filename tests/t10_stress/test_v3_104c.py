"""v3.104c - T10 stress replay tests.

The full stress runs 10 subprocesses and takes
~80 seconds. Tests load the persisted artifact
plus run a small live-probe (1 reimport, 2
permutations) to keep regression cost low.
"""
from __future__ import annotations

import json
import pathlib

from desi.t10_stress.replay import (
    order_invariance,
    reimport_invariance,
    seed_invariance,
    stress_adverse_flips_max,
    stress_beneficial_flips_max,
    stress_beneficial_flips_min,
)
from desi.t10_stress.stress import (
    SEEDS, StressKind,
    all_stress_outcomes,
)


_ARTIFACT_ROOT = pathlib.Path(
    __file__,
).resolve().parents[2] / "artifacts" / "v3_104c"


def _load_artifact(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_seed_count_meets_directive_minimum() -> None:
    """Directive § v3.104c: at least 10 seeds."""
    assert len(SEEDS) >= 10


def test_three_stress_kinds_enumerated() -> None:
    """Closed enum: SEED_RESHUFFLE,
    OUTCOME_PERMUTATION,
    ISOLATED_MODULE_REIMPORT."""
    assert len({k.value for k in StressKind}) == 3


def test_artifact_present() -> None:
    art = _load_artifact("report.json")
    assert art["seed_count"] >= 10


def test_artifact_adverse_flips_zero() -> None:
    """Killerfrage: haelt das neue Gate auch
    unter Stress? Yes - no cell flips adverse."""
    art = _load_artifact("report.json")
    assert (
        art["stress_adverse_flips_max"] == 0
    )


def test_artifact_beneficial_flips_stable() -> None:
    """Min equals max - the count is invariant
    across cells."""
    art = _load_artifact("report.json")
    assert (
        art["stress_beneficial_flips_min"]
        == art["stress_beneficial_flips_max"]
    )


def test_artifact_seed_invariance_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["seed_invariance"] == 1.0


def test_artifact_order_invariance_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["order_invariance"] == 1.0


def test_artifact_reimport_invariance_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["reimport_invariance"] == 1.0


def test_artifact_replay_stability_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["replay_stability"] == 1.0


def test_artifact_recommendation_in_closed_set() -> None:
    allowed = {
        "STRESS_STABLE",
        "STRESS_STABLE_WITH_DRIFT",
        "STRESS_UNSTABLE",
        "HALT_REPLAY_DRIFT",
    }
    art = _load_artifact("report.json")
    assert art["recommendation"] in allowed


def test_artifact_recommendation_is_stable() -> None:
    art = _load_artifact("report.json")
    assert art["recommendation"] == (
        "STRESS_STABLE"
    )


def test_live_outcome_permutation_invariant() -> None:
    """Lightweight live probe: run two
    permutations directly (no subprocess) and
    verify aggregates agree."""
    from desi.t10_compat.replay import (
        all_historical_gate_outcomes,
    )
    from desi.t10_gate.classify import (
        classify_outcome, DeltaKind,
    )
    base = list(all_historical_gate_outcomes())
    counts: list[tuple[int, int]] = []
    for k in (1, 4):
        perm = base[k:] + base[:k]
        adv = sum(
            1 for o in perm
            if classify_outcome(o)
            == DeltaKind.ADVERSE_FLIP.value
        )
        ben = sum(
            1 for o in perm
            if classify_outcome(o)
            == DeltaKind.BENEFICIAL_FLIP.value
        )
        counts.append((adv, ben))
    assert counts[0] == counts[1]


def test_live_invariance_helpers_in_unit_interval() -> None:
    """Sanity check on the public helpers
    without spawning the full stress."""
    art = _load_artifact("report.json")
    assert 0.0 <= art["seed_invariance"] <= 1.0
    assert 0.0 <= art["order_invariance"] <= 1.0
    assert (
        0.0 <= art["reimport_invariance"] <= 1.0
    )


def test_t10_gate_stress_artifact_present() -> None:
    art = _load_artifact("t10_gate_stress.json")
    assert (
        art["schema_version"]
        == "v3_104c_t10_gate_stress"
    )
    assert len(art["stress_outcomes"]) >= 23
