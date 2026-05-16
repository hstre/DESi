"""v3.13 regression — Aufgabe 1 + 7: every prior hash bit-identical."""
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
    assert m.precision == 1.000 and m.recall == 1.000
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


def test_v34_frame_benchmark_unchanged() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40 and m.fully_correct == 40


def test_v35_invariance_total_unchanged() -> None:
    assert len(FrameInvarianceRunner().run().results) == 400


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


def test_v311_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_11") == "1c8e6d0e0b90905c"


def test_v312_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_12") == "86d0d72251f7d589"


def test_v34_frame_ledger_event_set_unchanged() -> None:
    from desi.frames import FrameLedgerEventType
    assert {e.value for e in FrameLedgerEventType} == {
        "frame_compatibility_checked",
        "frame_conflict_detected",
        "frame_declaration_started",
        "frame_declared",
        "frame_pipeline_blocked",
        "frame_undeclared",
    }


def test_v311_runtime_ledger_event_set_unchanged() -> None:
    from desi.frame_tension import FrameTensionLedgerEvent
    assert {e.value for e in FrameTensionLedgerEvent} == {
        "frame_inheritance_allowed",
        "frame_inheritance_blocked",
        "frame_conflict_blocked",
        "frame_undecidable_blocked",
    }


def test_v313_router_does_not_modify_forbidden_roots() -> None:
    # logic/, recursive/, consilium/, tools/ must not import or
    # otherwise depend on the v3.13 router.
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = ("logic", "consilium", "recursive", "tools")
    pattern = re.compile(
        r"\bFrameTensionRouter\b|"
        r"\bframe_tension_integration\.router\b"
    )
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions FrameTensionRouter — directive violation"
            )
