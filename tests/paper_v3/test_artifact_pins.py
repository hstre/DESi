"""v3.24 — confirm every cited artifact hash matches the
deployed artifact."""
from __future__ import annotations

import pathlib

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

from ._helpers import load_artifact


_PINNED_ARTIFACTS = {
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


def test_v15_metrics_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000
    assert m.recall == 1.000


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
    assert m.total == 40
    assert m.fully_correct == 40


def test_all_artifact_hashes_pinned() -> None:
    drift: list[str] = []
    for name, expected in _PINNED_ARTIFACTS.items():
        try:
            artifact = load_artifact(name)
        except FileNotFoundError:
            drift.append(f"{name}: file missing")
            continue
        actual = artifact.get("replay_hash")
        if actual != expected:
            drift.append(
                f"{name}: pinned={expected}, actual={actual}"
            )
    assert drift == [], drift
