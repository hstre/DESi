"""v3.14 regression — Aufgabe 6: every prior hash bit-identical."""
from __future__ import annotations

import json
import pathlib
import re

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.frame_benchmark import FrameBenchmarkRunner, compute_frame_metrics
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


def test_v27_reconstruction_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v27_fail_case_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_v34_frame_benchmark_unchanged() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40 and m.fully_correct == 40


def test_v35_invariance_total_unchanged() -> None:
    assert len(FrameInvarianceRunner().run().results) == 400


def test_v311_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_11") == "1c8e6d0e0b90905c"


def test_v313_artifact_hash_pinned() -> None:
    assert _artifact_hash("v3_13") == "733032cc30a0cc2e"


def test_no_runtime_module_imports_heldout_causal() -> None:
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
        "frame_tension_audit", "frame_tension",
        "frame_tension_integration",
    )
    pattern = re.compile(r"heldout_causal")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions heldout_causal — directive violation"
            )
