"""Runtime + previous-bundle regression for v3.3."""
from __future__ import annotations

import pathlib
import re


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_forbidden_packages_do_not_import_cross_review() -> None:
    """v3.3 lives entirely under docs/, artifacts/, tests/ — no
    production module may depend on it."""
    src = _REPO_ROOT / "src" / "desi"
    pattern = re.compile(r"cross_review")
    for p in src.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert not pattern.search(text), (
            f"{p} mentions cross_review — directive violation"
        )


def test_v15_metrics_unchanged() -> None:
    import sys
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from desi.benchmark import BenchmarkRunner, compute_metrics
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000
    assert m.recall == 1.000
    assert m.false_positives == 0


def test_v19_tool_results_count() -> None:
    import sys
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from desi.tools import ToolBenchmarkRunner
    assert len(ToolBenchmarkRunner().run().results) == 20


def test_v3_2_reviewer_metrics_unchanged() -> None:
    """v3.2's seven-field reviewer-metrics gate must still hold."""
    import json
    p = _REPO_ROOT / "artifacts" / "v3_2" / "reviewer_metrics.json"
    payload = json.loads(p.read_text())
    assert payload["total_claims"] >= 50
    assert payload["verified_claims"] == payload["total_claims"]
    assert payload["commands_required"] <= 15
    assert payload["estimated_minutes"] <= 15
    assert payload["broken_links"] == 0
    assert payload["missing_paths"] == 0
    assert payload["hash_mismatches"] == 0
