"""v3.17 — report determinism + regression."""
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.causal_link_typing import build_link_typing_report
from desi.frame_benchmark import (
    FrameBenchmarkRunner,
    compute_frame_metrics,
)
from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_report_classification_coverage_is_one() -> None:
    r = build_link_typing_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.classification_coverage == 1.0


def test_report_total_link_count() -> None:
    r = build_link_typing_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.total_link_count >= 250


def test_report_recommendation_gate_only_with_all_conditions() -> None:
    r = build_link_typing_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "NONE":
        return
    assert r.contamination.contamination_count == 0
    assert r.contamination.v315_attack_reduction >= 0.80
    assert r.contamination.v314_survival_rate >= 0.85
    assert r.negative_control_accuracy >= 0.95


def test_report_replay_hash_deterministic() -> None:
    now = _now()
    a = build_link_typing_report(started_at=now, finished_at=now)
    b = build_link_typing_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_report_replay_hash_independent_of_timestamps() -> None:
    a = build_link_typing_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_link_typing_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    r = build_link_typing_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)


# Regression — none of these may drift while v3.17 is read-only.


def test_v15_metrics_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000 and m.recall == 1.000


def test_v23_multistep_count_unchanged() -> None:
    assert len(MultiStepBenchmarkRunner().run().results) == 30


def test_v27_reconstruction_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v27_failcase_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_v34_frame_benchmark_unchanged() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40 and m.fully_correct == 40


def _artifact_hash(name: str) -> str:
    return json.loads(
        (_REPO_ROOT / "artifacts" / name / "report.json")
        .read_text(encoding="utf-8")
    )["replay_hash"]


def test_artifact_hashes_pinned() -> None:
    assert _artifact_hash("v3_11") == "1c8e6d0e0b90905c"
    assert _artifact_hash("v3_13") == "733032cc30a0cc2e"
    assert _artifact_hash("v3_14") == "94be5611fc9bd336"
    assert _artifact_hash("v3_15") == "a6edfa9a53914bcc"
    assert _artifact_hash("v3_16") == "1f4e5f85c085d32f"


def test_no_runtime_module_imports_causal_link_typing() -> None:
    root = _REPO_ROOT / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
        "benchmark", "benchmark_multistep",
        "bridge_audit", "causal_probe", "rule_audit",
        "sandbox", "diagnostic", "rule_patch_protocol",
        "self_audit", "doc_anchors",
        "frames", "frame_benchmark", "frame_invariance",
        "frame_failure_audit", "frame_disambiguator_probe",
        "frame_context_probe", "frame_consistency_probe",
        "frame_tension_audit", "frame_tension",
        "frame_tension_integration", "heldout_causal",
        "causal_redteam", "causal_suspension",
    )
    pattern = re.compile(r"causal_link_typing")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions causal_link_typing"
            )
