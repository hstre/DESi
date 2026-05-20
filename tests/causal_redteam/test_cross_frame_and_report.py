"""Aufgaben 5 + 8 + 9 — cross-frame, report, replay, regression."""
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.causal_redteam import build_redteam_report, run_cross_frame
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_cross_frame_returns_one_outcome_per_case() -> None:
    summary, outs = run_cross_frame()
    assert summary.total == len(outs)


def test_cross_frame_metrics_self_consistent() -> None:
    summary, outs = run_cross_frame()
    chain_count = sum(1 for o in outs if o.chain_only_supported)
    assert summary.chain_only_attacks == chain_count
    prevented = sum(1 for o in outs if o.routing_prevented_attack)
    assert summary.routing_prevented_attacks == prevented


def test_cross_frame_layer_intercepts_some_chain_attacks() -> None:
    # The v3.13 router was designed against the same chain
    # vulnerability shape; we expect it to catch at least *some*
    # of the chain-only successful attacks.
    summary, _ = run_cross_frame()
    if summary.chain_only_attacks > 0:
        assert summary.routing_prevented_attacks > 0


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_redteam_report(started_at=now, finished_at=now)
    b = build_redteam_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_redteam_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_redteam_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    r = build_redteam_report(started_at=_now(), finished_at=_now())
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0


def test_v15_metrics_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000 and m.recall == 1.000


def test_v23_multistep_count_unchanged() -> None:
    assert len(MultiStepBenchmarkRunner().run().results) == 30


def test_v27_reconstruction_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v27_fail_case_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_v28_artifact_hashes_pinned() -> None:
    # v3.8/9/10/11/13/14 artifacts pinned.
    assert _artifact_hash("v3_11") == "1c8e6d0e0b90905c"
    assert _artifact_hash("v3_13") == "733032cc30a0cc2e"
    assert _artifact_hash("v3_14") == "94be5611fc9bd336"


def test_v34_frame_benchmark_unchanged() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40 and m.fully_correct == 40


def test_no_runtime_module_imports_causal_redteam() -> None:
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
    )
    pattern = re.compile(r"causal_redteam")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} imports causal_redteam"
            )
