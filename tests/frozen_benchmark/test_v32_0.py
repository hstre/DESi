"""v32.0 - Frozen Baseline Reconstruction tests."""
from __future__ import annotations

import json
import pathlib

from desi.frozen_baseline import (
    FROZEN_DISABLED_FEATURES, FROZEN_VERSION, artifact_identity,
    baseline_fingerprint, baseline_identity, baseline_recomputes,
    baseline_reproducibility, baseline_run, baseline_workload,
    build_baseline_artifact, build_report, frozen_guarantee,
    governance_identity, is_frozen, replay_stability,
    uses_evolution_features,
)
from desi.frozen_baseline.report import (
    REPORT_VERDICTS, VERDICT_FROZEN,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "frozen_benchmark"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- frozen baseline ----------------------------
def test_baseline_is_frozen() -> None:
    assert is_frozen() is True
    assert frozen_guarantee() is True
    assert uses_evolution_features() is False


def test_disabled_evolution_features() -> None:
    assert set(FROZEN_DISABLED_FEATURES) == {
        "replay_cache_evolution", "mutation_ecology",
        "evolution_memory", "peripheral_mutation",
        "long_horizon_branching",
    }


def test_baseline_has_no_cache() -> None:
    # without a cache, every repeat is a real recompute
    assert baseline_recomputes() == sum(
        w.repeat for w in baseline_workload()
    )
    assert baseline_recomputes() == 36


def test_baseline_identity_full() -> None:
    assert baseline_identity() == 1.0
    assert baseline_fingerprint() == baseline_fingerprint()


def test_artifact_identity_full() -> None:
    assert artifact_identity() == 1.0


def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0


def test_baseline_reproducibility_full() -> None:
    assert baseline_reproducibility() == 1.0
    assert baseline_run().to_dict() == baseline_run().to_dict()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        baseline_identity(), artifact_identity(),
        governance_identity(), baseline_reproducibility(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_frozen() -> None:
    assert build_report().recommendation == VERDICT_FROZEN


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v32_0_baseline.json")
    assert art["schema_version"] == "v32_0_frozen_baseline"


def test_artifact_baseline_version() -> None:
    art = _load("v32_0_baseline.json")
    assert art["baseline_version"] == FROZEN_VERSION
    assert art["baseline_version"] == "DESi_baseline_frozen_v1"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v32_0_baseline.json")
    disc = art["disclaimer"].lower()
    assert "pre-v29" in disc
    assert "must stay frozen" in disc
    assert "there is no" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v32_0_baseline.json")
    required = {
        "baseline_identity", "artifact_identity",
        "governance_identity", "baseline_reproducibility",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v32_0_baseline.json")
    live = build_baseline_artifact()
    assert art == live
