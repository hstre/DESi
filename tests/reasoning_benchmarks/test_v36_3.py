"""v36.3 - Multi-Hop Reasoning (MuSiQue / HotpotQA) tests."""
from __future__ import annotations

import json
import pathlib

from desi.reasoning_benchmarks_multihop import (
    all_tasks, build_multihop_artifact, build_report,
    compressed_chain, detected_gaps, evidence_path_visibility,
    hop_chain_integrity, hotpotqa_tasks, missing_hop_detection,
    missing_hops, multihop_metrics, musique_tasks,
    redundant_hop_compression, redundant_hops, replay_stability,
    spurious_hops,
)
from desi.reasoning_benchmarks_multihop.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "reasoning_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- datasets -----------------------------------
def test_datasets_loaded() -> None:
    assert len(musique_tasks()) == 3
    assert len(hotpotqa_tasks()) == 3
    assert len(all_tasks()) == 6


# --- chain integrity / evidence -----------------
def test_hop_chain_integrity_full() -> None:
    assert hop_chain_integrity() == 1.0


def test_no_spurious_hops() -> None:
    for t in all_tasks():
        assert spurious_hops(t) == ()


def test_evidence_path_visibility_full() -> None:
    assert evidence_path_visibility() == 1.0


# --- redundant compression ----------------------
def test_redundant_hop_compression_full() -> None:
    assert redundant_hop_compression() == 1.0


def test_compression_is_lossless() -> None:
    for t in all_tasks():
        chain = set(compressed_chain(t))
        assert not (chain & set(redundant_hops(t)))
        present_required = {
            r for r in t.required_hops
            if r in {h.hop_id for h in t.hops}
        }
        assert present_required.issubset(chain)


# --- missing hop detection (gaps not hidden) ----
def test_missing_hop_detection_full() -> None:
    assert missing_hop_detection() == 1.0


def test_gaps_are_surfaced() -> None:
    gaps = detected_gaps()
    assert "mq_003" in gaps
    assert "h2" in gaps["mq_003"]
    assert "hp_003" in gaps


def test_complete_tasks_have_no_gaps() -> None:
    by_id = {t.task_id: t for t in all_tasks()}
    assert missing_hops(by_id["mq_001"]) == ()
    assert missing_hops(by_id["hp_001"]) == ()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in multihop_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_governance_identity() -> None:
    assert build_report().governance_identity == 1.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v36_3_multihop.json")
    assert art["schema_version"] == "v36_3_multihop_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v36_3_multihop.json")
    disc = art["disclaimer"].lower()
    assert "surfaced rather than hidden" in disc
    assert "not official leaderboard results" in disc


def test_artifact_records_gaps() -> None:
    art = _load("v36_3_multihop.json")
    assert "mq_003" in art["detected_gaps"]


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v36_3_multihop.json")
    required = {
        "hop_chain_integrity", "evidence_path_visibility",
        "redundant_hop_compression", "missing_hop_detection",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v36_3_multihop.json")
    assert art == build_multihop_artifact()
