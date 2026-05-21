"""v29.1 - Real Replay Cache Branch tests."""
from __future__ import annotations

import json
import pathlib

from desi.replay_cache_evolution import (
    baseline_recompute_count, output_hashes as baseline_hashes,
)
from desi.replay_cache_real import (
    DeterministicCache, artifact_hash_stability,
    build_branch_artifact, build_report, cached_output_hashes,
    cached_recompute_count, fingerprint, governance_preservation,
    is_stale, perturbed_fingerprint, render_reuse_is_exact,
    replay_stability, runtime_reduction, stale_rejected_for,
    stale_state_rejection, valid_reuse_for,
)
from desi.replay_cache_evolution import workloads
from desi.replay_cache_real.report import (
    REPORT_VERDICTS, VERDICT_REAL,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "replay_cache_evolution"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real measured reduction --------------------
def test_runtime_reduction_above_floor() -> None:
    assert runtime_reduction() >= 0.20


def test_cached_recomputes_one_per_distinct_workload() -> None:
    assert cached_recompute_count() == len(workloads())
    assert cached_recompute_count() < baseline_recompute_count()


# --- byte-identical artifacts (no drift) --------
def test_artifact_hash_stability_full() -> None:
    assert artifact_hash_stability() == 1.0


def test_cached_outputs_equal_baseline() -> None:
    assert cached_output_hashes() == baseline_hashes()


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


# --- stale-state rejection (lineage-aware) ------
def test_stale_state_rejection_full() -> None:
    assert stale_state_rejection() == 1.0


def test_every_workload_rejects_stale_keys() -> None:
    for w in workloads():
        assert stale_rejected_for(w)
        assert valid_reuse_for(w)


def test_perturbed_fingerprint_is_stale() -> None:
    for w in workloads():
        valid = fingerprint(w)
        for comp in ("name", "seed", "work", "repeat",
                     "governance"):
            assert is_stale(valid, perturbed_fingerprint(w, comp))


# --- governance untouched -----------------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


# --- deterministic cache, no hidden state -------
def test_cache_is_deterministic_per_run() -> None:
    c1 = DeterministicCache()
    c2 = DeterministicCache()
    w = workloads()[0]
    assert c1.get_or_rebuild(w) == c2.get_or_rebuild(w)
    # second call on same cache is a hit, identical value
    assert c1.get_or_rebuild(w) == c1.get_or_rebuild(w)
    assert c1.counter.hits >= 1


def test_render_reuse_exact() -> None:
    assert render_reuse_is_exact() is True


def test_metrics_in_unit_interval() -> None:
    for m in (
        runtime_reduction(), artifact_hash_stability(),
        stale_state_rejection(), governance_preservation(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_real() -> None:
    assert build_report().recommendation == VERDICT_REAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v29_1_branch.json")
    assert art["schema_version"] == "v29_1_replay_cache_branch"


def test_artifact_is_branch_isolated() -> None:
    art = _load("v29_1_branch.json")
    assert art["branch"] == "proposal/replay_cache_v1"
    assert art["branch"] != "main"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v29_1_branch.json")
    disc = art["disclaimer"].lower()
    assert "byte-identical" in disc
    assert "no hidden mutable state" in disc
    assert "nothing is merged" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v29_1_branch.json")
    required = {
        "runtime_reduction", "artifact_hash_stability",
        "stale_state_rejection", "governance_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v29_1_branch.json")
    live = build_branch_artifact()
    assert art == live
