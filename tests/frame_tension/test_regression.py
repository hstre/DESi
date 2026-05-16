"""v3.11 regression — Aufgaben 1 + 8: every prior hash bit-identical."""
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


def _artifact_hash(name: str) -> str:
    return json.loads(
        (_REPO_ROOT / "artifacts" / name / "report.json")
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
    assert _artifact_hash("v3_8") == "84eb20223fea09e0"


def test_v39_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_9") == "dbc8da87ab466bef"


def test_v310_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_10") == "26bd447ace08c0ac"


def test_v34_frame_ledger_event_set_unchanged() -> None:
    # The existing v3.4 FrameLedger event taxonomy must not gain
    # or lose members. v3.11 adds a *separate* ledger.
    from desi.frames import FrameLedgerEventType
    assert {e.value for e in FrameLedgerEventType} == {
        "frame_compatibility_checked",
        "frame_conflict_detected",
        "frame_declaration_started",
        "frame_declared",
        "frame_pipeline_blocked",
        "frame_undeclared",
    }


def test_no_forbidden_root_imports_frame_tension_runtime() -> None:
    # The directive forbids touching logic/, recursive/, tools/,
    # consilium/. None of them may even *import* the new runtime
    # module. (Frames/ may not import it either — it's a layer
    # above the detector.)
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
        "frame_tension_audit",
    )
    pattern = re.compile(r"\bfrom\s+\.\.frame_tension\b|"
                         r"\bdesi\.frame_tension\b")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} imports frame_tension — directive violation"
            )
