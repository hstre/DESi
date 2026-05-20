"""v4.3 — regression: protected benchmarks remain green and
all prior pinned hashes (except v4.0/v4.1/v4.2 which v4.3
explicitly perturbs) stay stable."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.frame_benchmark import (
    FrameBenchmarkRunner, compute_frame_metrics,
)
from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_v15_main_benchmark_pristine() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000
    assert m.recall == 1.000


def test_v23_multistep_count_preserved() -> None:
    r = MultiStepBenchmarkRunner().run()
    assert len(r.results) == 30


def test_v27_reconstruction_hash_preserved() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v27_failcase_hash_preserved() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_v34_frame_benchmark_preserved() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.total == 40
    assert m.fully_correct == 40


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


def test_v40_v41_v42_historical_artifacts_preserved() -> None:
    """v4.3 must not rewrite the historical artifact files. The
    on-disk JSON for v4.0/v4.1/v4.2 still carries the pre-v4.3
    hashes; the rebuild under the v4.3 patched auditor produces
    *new* hashes, which is expected and documented in
    docs/memory/v4_3.md."""
    for name, expected in (
        ("v4_0", "aefa8f1e3429225a"),
        ("v4_1", "f7ec695f17aa341b"),
        ("v4_2", "181ec3cb1febf62f"),
    ):
        p = _REPO_ROOT / "artifacts" / name / "report.json"
        actual = json.loads(
            p.read_text(encoding="utf-8")
        )["replay_hash"]
        assert actual == expected, (name, actual)
