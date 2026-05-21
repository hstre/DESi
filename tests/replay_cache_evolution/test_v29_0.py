"""v29.0 - Baseline Measurement tests."""
from __future__ import annotations

import json
import pathlib

from desi.replay_cache_evolution import (
    all_anchors, anchors_stable, artifact_stability,
    baseline_recompute_count, baseline_run,
    build_baseline_artifact, build_report,
    cache_opportunity_visibility, output_hashes, rebuild,
    recompute_visibility, replay_stability, runtime_visibility,
    workloads,
)
from desi.replay_cache_evolution.report import (
    REPORT_VERDICTS, VERDICT_VISIBLE,
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


# --- workloads & cost visibility ----------------
def test_workloads_present_and_cacheable() -> None:
    ws = workloads()
    assert len(ws) >= 1
    for w in ws:
        assert w.repeat >= 1
        assert w.is_cacheable() == (w.repeat > 1)


def test_baseline_recompute_count_is_sum_of_repeats() -> None:
    assert baseline_recompute_count() == sum(
        w.repeat for w in workloads()
    )
    counter, _ = baseline_run()
    assert counter.misses == baseline_recompute_count()
    assert counter.hits == 0


def test_runtime_visibility_full() -> None:
    assert runtime_visibility() == 1.0


def test_recompute_visibility_full() -> None:
    assert recompute_visibility() == 1.0


def test_cache_opportunity_visibility_full() -> None:
    assert cache_opportunity_visibility() == 1.0


# --- rebuild is real & deterministic ------------
def test_rebuild_deterministic() -> None:
    assert rebuild("x", 500) == rebuild("x", 500)
    assert rebuild("x", 500) != rebuild("y", 500)


# --- artifact stability -------------------------
def test_artifact_stability_full() -> None:
    assert artifact_stability() == 1.0


def test_output_hashes_stable() -> None:
    assert output_hashes() == output_hashes()


def test_anchors_stable() -> None:
    assert anchors_stable() is True
    assert all_anchors() == all_anchors()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        runtime_visibility(), artifact_stability(),
        recompute_visibility(), cache_opportunity_visibility(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_visible() -> None:
    assert build_report().recommendation == VERDICT_VISIBLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- no wall-clock in deterministic outputs -----
def _all_keys(obj) -> set:
    keys: set = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= _all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            keys |= _all_keys(v)
    return keys


def test_no_wallclock_field_in_artifact() -> None:
    # no stored timing field (the disclaimer may *mention*
    # wall-clock as prose; what matters is no timing is persisted)
    keys = {k.lower() for k in _all_keys(build_baseline_artifact())}
    for forbidden in (
        "seconds", "elapsed", "wall_clock", "wallclock",
        "_ms", "duration",
    ):
        assert not any(forbidden in k for k in keys)


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v29_0_baseline.json")
    assert art["schema_version"] == (
        "v29_0_replay_cache_baseline"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v29_0_baseline.json")
    disc = art["disclaimer"].lower()
    assert "recompute operations" in disc
    assert "never stored" in disc
    assert "nothing is changed" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v29_0_baseline.json")
    required = {
        "runtime_visibility", "artifact_stability",
        "recompute_visibility", "cache_opportunity_visibility",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v29_0_baseline.json")
    live = build_baseline_artifact()
    assert art == live
