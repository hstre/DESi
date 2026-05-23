"""v34.2 - Output Drift & Reproducibility Benchmark Run tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_runs_repro import (
    REPEATS, artifact_identity, build_report,
    build_reproducibility_artifact, citation_identity,
    determinism_scorecards, metric_identity, output_identity,
    replay_hash_identity, replay_stability, reproducibility_metrics,
    section_identity, snapshots,
)
from desi.benchmark_runs_repro.report import (
    REPORT_VERDICTS, VERDICT_REPRODUCIBLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_runs"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- repeated runs ------------------------------
def test_repeats_at_least_five() -> None:
    assert REPEATS >= 5
    assert len(snapshots()) == REPEATS


def test_snapshots_all_identical() -> None:
    snaps = snapshots()
    first = snaps[0]
    for s in snaps:
        assert s == first


# --- identity metrics ---------------------------
def test_output_identity_full() -> None:
    assert output_identity() == 1.0


def test_metric_identity_full() -> None:
    assert metric_identity() == 1.0


def test_citation_identity_full() -> None:
    assert citation_identity() == 1.0


def test_artifact_identity_full() -> None:
    assert artifact_identity() == 1.0


def test_section_identity_full() -> None:
    assert section_identity() == 1.0


def test_replay_hash_identity_full() -> None:
    assert replay_hash_identity() == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in reproducibility_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecards ---------------------------------
def test_scorecards_all_identical() -> None:
    cards = determinism_scorecards()
    assert len(cards) == 6
    for c in cards:
        assert c.identical is True
        assert c.signature


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_reproducible() -> None:
    assert build_report().recommendation == VERDICT_REPRODUCIBLE


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v34_2_reproducibility.json")
    assert art["schema_version"] == "v34_2_reproducibility_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v34_2_reproducibility.json")
    disc = art["disclaimer"].lower()
    assert "byte-identical" in disc
    assert "recomputed from scratch" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v34_2_reproducibility.json")
    required = {
        "output_identity", "metric_identity", "citation_identity",
        "artifact_identity", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v34_2_reproducibility.json")
    assert art == build_reproducibility_artifact()
