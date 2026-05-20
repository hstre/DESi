"""v4.4 — read-only/import-only invariants + historical pins."""
from __future__ import annotations

import json
import pathlib
import re


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_no_runtime_module_imports_residual_semantic_probe() -> None:
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
        "epistemic_trajectory", "premise_audit",
        "gate_ablation", "gate_order", "gate_latency",
        "external_probe", "frame_inference",
        "external_audit_probe", "external_audit_patch",
    )
    pattern = re.compile(r"residual_semantic_probe")
    for sub in forbidden:
        sub_path = root / sub
        if not sub_path.exists():
            continue
        for p in sub_path.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions residual_semantic_probe"
            )


def test_v44_does_not_edit_forbidden_runtime_files() -> None:
    forbidden_roots = (
        _REPO_ROOT / "src" / "desi" / "logic",
        _REPO_ROOT / "src" / "desi" / "frames",
        _REPO_ROOT / "src" / "desi" / "frame_tension",
        _REPO_ROOT / "src" / "desi" / "frame_inference",
        _REPO_ROOT / "src" / "desi" / "recursive",
        _REPO_ROOT / "src" / "desi" / "consilium",
        _REPO_ROOT / "src" / "desi" / "tools",
    )
    for root in forbidden_roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert "residual_semantic_probe" not in text, p


_V3_EXPECTED: dict[str, str] = {
    "v3_11": "1c8e6d0e0b90905c",
    "v3_13": "733032cc30a0cc2e",
    "v3_14": "94be5611fc9bd336",
    "v3_15": "a6edfa9a53914bcc",
    "v3_16": "1f4e5f85c085d32f",
    "v3_17": "a01b6edaa9e1a086",
    "v3_18": "7829ae1e1750f00d",
    "v3_19": "3cbde141b5d90a46",
    "v3_20": "02eb32df1f51b761",
    "v3_21": "f570c9e94770dfbc",
    "v3_22": "be039cd52c3de9b5",
    "v3_23": "0246444ccd8f96ef",
}


def test_v3_artifact_hashes_pinned() -> None:
    actual = {}
    for name in _V3_EXPECTED:
        p = _REPO_ROOT / "artifacts" / name / "report.json"
        actual[name] = json.loads(
            p.read_text(encoding="utf-8")
        )["replay_hash"]
    assert actual == _V3_EXPECTED


def test_v40_v41_v42_v43_historical_artifacts_preserved() -> None:
    for name, expected in (
        ("v4_0", "aefa8f1e3429225a"),
        ("v4_1", "f7ec695f17aa341b"),
        ("v4_2", "181ec3cb1febf62f"),
        ("v4_3", "7c63bcae4cf3fb37"),
    ):
        p = _REPO_ROOT / "artifacts" / name / "report.json"
        actual = json.loads(
            p.read_text(encoding="utf-8")
        )["replay_hash"]
        assert actual == expected, (name, actual)
