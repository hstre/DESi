"""HF benchmark runner tests (PERIPHERAL, offline, targeted).

Verifies the HF runner is benchmark periphery and nothing more: it loads an
HF-format dataset offline, runs it through the tested boundary, stays
replay-stable and governance-independent, refuses core mutation, and treats
claims only as projections. No network, no core import/mutation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

# load the runner module from the benchmarks/ tree (not an installed package)
_RUNNER = _REPO / "benchmarks" / "hf_benchmark" / "hf_runner.py"
_spec = importlib.util.spec_from_file_location("hf_runner", _RUNNER)
hf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hf)

from desi.benchmark_ports import ExtractorPort  # noqa: E402

_SAMPLE = _REPO / "benchmarks" / "hf_benchmark" / "sample_hf_tasks.jsonl"


def test_offline_loader_normalizes() -> None:
    tasks = hf.load_hf_tasks(offline_path=_SAMPLE, limit=100)
    assert len(tasks) == 5
    for t in tasks:
        assert set(t) == {"task_id", "question", "answer"}
        assert t["task_id"].startswith("hf-")


def test_local_extractor_is_a_port() -> None:
    ext = hf.LocalExtractor()
    assert isinstance(ext, ExtractorPort)
    proj = ext.extract({"question": "q", "answer": "a"})
    # claims are projections: (label, value) pairs
    assert proj == (("answer", "a"),)


def test_runner_replay_stable_and_governed() -> None:
    tasks = hf.load_hf_tasks(offline_path=_SAMPLE)
    res = hf.run_hf_benchmark(tasks)
    assert res["n"] == 5
    assert res["replay_stable"] is True
    assert res["gov_independent"] is True
    assert res["all_traceable"] is True
    # critical branches preserved by the tested adapter
    assert res["core_metrics"].get("critical_branch_preservation") == 1.0


def test_runner_refuses_core_mutation() -> None:
    tasks = hf.load_hf_tasks(offline_path=_SAMPLE)
    res = hf.run_hf_benchmark(tasks, steer_probe=5)
    assert res["mutation_attempts"] == 5
    assert res["mutation_rejected"] == 5
    assert res["mutation_requested"] == 5


def test_hf_dataset_without_library_errors_cleanly() -> None:
    # requesting the hub source without the optional lib must fail loudly,
    # never silently hit the network
    try:
        import datasets  # noqa: F401
    except Exception:
        import pytest
        with pytest.raises(RuntimeError):
            hf.load_hf_tasks(dataset="nonexistent/dataset", offline_path=None)
