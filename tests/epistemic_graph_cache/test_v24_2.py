"""v24.2 - Epistemic Replay Cache tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_graph_cache import (
    COMPONENTS, ReplayCache, build_cache_artifact, build_report,
    cache_validity, cold_cache, components_match,
    compute_reduction, current_fingerprints, invalidation_integrity,
    is_stale, replay_stability, replay_stats, reuse_is_validated,
    stale_detection, subspaces,
)
from desi.epistemic_graph_cache.report import (
    REPORT_VERDICTS, VERDICT_SAFE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "epistemic_graph"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- the five-component cache rule --------------
def test_five_identity_components() -> None:
    assert COMPONENTS == (
        "replay_hashes", "fixtures", "governance", "claims",
        "metrics",
    )


def test_subspaces_built_from_graph() -> None:
    subs = subspaces()
    assert len(subs) >= 1
    for s in subs:
        assert s.fingerprint()
        assert s.claims  # each subspace owns its claim


def test_fingerprint_changes_with_each_component() -> None:
    for s in subspaces():
        base = s.fingerprint()
        for comp in COMPONENTS:
            assert s.perturbed(comp).fingerprint() != base


# --- compute reduction --------------------------
def test_compute_reduction_on_identical_replay() -> None:
    assert compute_reduction() == 1.0
    st = replay_stats()
    assert st["reused"] == st["total"]
    assert st["recomputed"] == 0


# --- validity -----------------------------------
def test_cache_validity_full() -> None:
    assert cache_validity() == 1.0


def test_reuse_is_validated() -> None:
    assert reuse_is_validated() is True


def test_components_match_self() -> None:
    for s in subspaces():
        assert components_match(s, s)


# --- stale detection ----------------------------
def test_stale_detection_full() -> None:
    assert stale_detection() == 1.0


def test_changed_component_is_stale() -> None:
    cache = cold_cache()
    for s in subspaces():
        for comp in COMPONENTS:
            changed = s.perturbed(comp)
            assert is_stale(
                cache, s.subspace_id, changed.fingerprint(),
            )


def test_identical_fingerprint_not_stale() -> None:
    cache = cold_cache()
    for s in subspaces():
        assert not is_stale(
            cache, s.subspace_id, s.fingerprint(),
        )


# --- invalidation -------------------------------
def test_invalidation_integrity_full() -> None:
    assert invalidation_integrity() == 1.0


def test_invalidate_removes_entry() -> None:
    cache = cold_cache()
    s = subspaces()[0]
    assert cache.invalidate(s.subspace_id) is True
    assert not cache.lookup(s.subspace_id, s.fingerprint())
    assert cache.invalidate(s.subspace_id) is False


# --- replay stability ---------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_fingerprints_stable() -> None:
    assert current_fingerprints() == current_fingerprints()


def test_metrics_in_unit_interval() -> None:
    for m in (
        compute_reduction(), cache_validity(),
        stale_detection(), invalidation_integrity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_safe() -> None:
    assert build_report().recommendation == VERDICT_SAFE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v24_2_cache.json")
    assert art["schema_version"] == (
        "v24_2_epistemic_replay_cache"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v24_2_cache.json")
    disc = art["disclaimer"].lower()
    assert "replay-validated" in disc
    assert "not opportunistic" in disc
    assert "no epistemic drift" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v24_2_cache.json")
    required = {
        "compute_reduction", "cache_validity",
        "stale_detection", "invalidation_integrity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_cache_key_components() -> None:
    art = _load("v24_2_cache.json")
    assert art["cache_key_components"] == list(COMPONENTS)


def test_artifact_full_matches_live_build() -> None:
    art = _load("v24_2_cache.json")
    live = build_cache_artifact()
    assert art == live
