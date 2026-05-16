"""v3.10 regression — runtime untouched, all prior hashes pinned."""
from __future__ import annotations

import json
import pathlib
import re

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.frame_benchmark import FrameBenchmarkRunner, compute_frame_metrics
from desi.frame_failure_audit import build_audit_report
from desi.frame_invariance import FrameInvarianceRunner
from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    compute_benchmark_hashes,
    fake_rule_without_guards_candidate,
)
from desi.tools import ToolBenchmarkRunner


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _v3_8_hash() -> str:
    return json.loads(
        (_REPO_ROOT / "artifacts" / "v3_8" / "report.json")
        .read_text(encoding="utf-8")
    )["replay_hash"]


def _v3_9_hash() -> str:
    return json.loads(
        (_REPO_ROOT / "artifacts" / "v3_9" / "report.json")
        .read_text(encoding="utf-8")
    )["replay_hash"]


def test_v15_metrics_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000
    assert m.recall == 1.000
    assert m.false_positives == 0


def test_v19_tool_count_unchanged() -> None:
    assert len(ToolBenchmarkRunner().run().results) == 20


def test_v23_multistep_count_unchanged() -> None:
    assert len(MultiStepBenchmarkRunner().run().results) == 30


def test_v28_reconstruction_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v28_fail_case_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_compute_benchmark_hashes_stable() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_v34_frame_benchmark_unchanged() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40
    assert m.fully_correct == 40


def test_v35_invariance_total_unchanged() -> None:
    run = FrameInvarianceRunner().run()
    assert len(run.results) == 400


def test_v36_failure_audit_thirty_failures() -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    rep = build_audit_report(started_at=now, finished_at=now)
    assert rep.total_failures == 30


def test_v38_artifact_hash_pinned() -> None:
    # Aufgabe 9: v3.8 context probe replay_hash bit-identical.
    assert _v3_8_hash() == "84eb20223fea09e0"


def test_v39_artifact_hash_pinned() -> None:
    # Aufgabe 9: v3.9 consistency probe replay_hash bit-identical.
    assert _v3_9_hash() == "dbc8da87ab466bef"


def test_no_runtime_module_imports_frame_tension_audit() -> None:
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
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
    )
    pattern = re.compile(r"frame_tension_audit")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions frame_tension_audit — directive violation"
            )
