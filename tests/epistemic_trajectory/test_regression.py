"""v3.19 — runtime regression: read-only, all hashes pinned."""
from __future__ import annotations

import json
import pathlib
import re

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
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


def _artifact_hash(name: str) -> str:
    return json.loads(
        (_REPO_ROOT / "artifacts" / name / "report.json")
        .read_text(encoding="utf-8")
    )["replay_hash"]


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


def test_artifact_hashes_pinned() -> None:
    assert _artifact_hash("v3_11") == "1c8e6d0e0b90905c"
    assert _artifact_hash("v3_13") == "733032cc30a0cc2e"
    assert _artifact_hash("v3_14") == "94be5611fc9bd336"
    assert _artifact_hash("v3_15") == "a6edfa9a53914bcc"
    assert _artifact_hash("v3_16") == "1f4e5f85c085d32f"
    assert _artifact_hash("v3_17") == "a01b6edaa9e1a086"
    assert _artifact_hash("v3_18") == "7829ae1e1750f00d"


def test_no_runtime_module_imports_epistemic_trajectory() -> None:
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
        "causal_link_typing", "causal_naturalness",
    )
    pattern = re.compile(r"epistemic_trajectory")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions epistemic_trajectory"
            )
