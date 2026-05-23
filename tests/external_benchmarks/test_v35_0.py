"""v35.0 - External Dataset Connector Layer tests."""
from __future__ import annotations

import json
import pathlib

from desi.external_benchmarks import (
    BENCHMARK_FAMILIES, PROVENANCE_OFFLINE_REFERENCE,
    all_normalized_tasks, available_datasets,
    build_connectors_artifact, build_report, connector_metrics,
    dataset_hash_visibility, dataset_version_visibility,
    governance_independence, load_all, load_dataset, network_free,
    normalized_tasks, replay_stability, task_normalization_integrity,
)
from desi.external_benchmarks.report import (
    REPORT_VERDICTS, VERDICT_INGESTED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "external_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- network-free / datasets --------------------
def test_network_free() -> None:
    assert network_free() is True


def test_datasets_available() -> None:
    names = available_datasets()
    assert "beliefshift_ref" in names
    assert "memevo_ref" in names
    assert "agentdrift_ref" in names
    assert "toolchain_ref" in names


def test_families_registered() -> None:
    for fam in ("BeliefShift", "MemEvoBench", "AgentDrift",
                "ToolChain"):
        assert fam in BENCHMARK_FAMILIES


# --- versioning / hashing -----------------------
def test_dataset_version_visibility_full() -> None:
    assert dataset_version_visibility() == 1.0


def test_dataset_hash_visibility_full() -> None:
    assert dataset_hash_visibility() == 1.0


def test_every_dataset_has_hashes() -> None:
    for d in load_all():
        assert d.byte_hash
        assert d.content_hash
        assert d.version
        assert d.provenance == PROVENANCE_OFFLINE_REFERENCE


def test_hashes_reproducible() -> None:
    a = load_dataset("toolchain_ref").content_hash
    b = load_dataset("toolchain_ref").content_hash
    assert a == b


def test_provenance_not_live_download() -> None:
    # honesty: vendored reference data, not a live official suite
    for d in load_all():
        assert d.is_live_download() is False


# --- normalisation ------------------------------
def test_task_normalization_integrity_full() -> None:
    assert task_normalization_integrity() == 1.0


def test_normalized_tasks_bound_to_dataset() -> None:
    tasks = all_normalized_tasks()
    assert tasks
    for t in tasks:
        assert t.is_complete()
        assert t.dataset_content_hash
        assert t.dataset_version
        assert t.provenance == PROVENANCE_OFFLINE_REFERENCE


def test_beliefshift_normalizes_to_drift() -> None:
    tasks = normalized_tasks("BeliefShift")
    assert tasks
    for t in tasks:
        assert t.route == "drift"


# --- governance / replay ------------------------
def test_governance_independence_full() -> None:
    assert governance_independence() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in connector_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_ingested() -> None:
    assert build_report().recommendation == VERDICT_INGESTED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v35_0_connectors.json")
    assert art["schema_version"] == "v35_0_external_connectors"


def test_artifact_carries_honest_disclaimer() -> None:
    art = _load("v35_0_connectors.json")
    disc = art["disclaimer"].lower()
    assert "network-free" in disc
    assert "not live downloads" in disc
    assert "not official leaderboard results" in disc


def test_artifact_datasets_listed() -> None:
    art = _load("v35_0_connectors.json")
    assert len(art["datasets"]) == 4
    assert art["network_free"] is True


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v35_0_connectors.json")
    required = {
        "dataset_version_visibility", "dataset_hash_visibility",
        "task_normalization_integrity", "governance_independence",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v35_0_connectors.json")
    assert art == build_connectors_artifact()
