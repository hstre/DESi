"""Reproduction test for the DriftBench compression headline numbers.

Pins every figure reported in README Section 7.1 to the committed dataset
``data/driftbench/driftbench_compression.jsonl``. If the data or the
computation drift, these assertions fail — the paper's numbers are no longer
"asserted only" but bound to a runnable check.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from reproduce_driftbench import DATA, compute, load  # noqa: E402


@pytest.fixture(scope="module")
def stats() -> dict:
    assert DATA.exists(), f"dataset missing: {DATA}"
    return compute(load())


def test_trajectory_count(stats):
    assert stats["n"] == 1525


def test_mean_tokens(stats):
    # README: mean raw 9,900 ; mean DESi state 269
    assert round(stats["mean_raw_tokens"]) == 9900
    assert round(stats["mean_desi_tokens"]) == 269


def test_compression_ratio_965(stats):
    # README: mean compression 96.5%
    assert round(stats["mean_compression_ratio"] * 100, 1) == 96.5


def test_all_trajectories_over_90pct(stats):
    # README: 1525/1525 achieve >90% compression
    assert stats["frac_over_90pct"] == 1.0


def test_drift_correlations(stats):
    # README: raw proxy 0.438 ; DESi summary 0.466
    assert round(stats["corr_raw"], 3) == 0.438
    assert round(stats["corr_desi"], 3) == 0.466


def test_preservation_ratio_rho(stats):
    # README: drift signal preservation ratio rho = 1.06
    assert round(stats["rho"], 2) == 1.06


def test_structural_preservation_flags(stats):
    # README: all four structural families preserved 1525/1525
    for flag, count in stats["preservation"].items():
        assert count == 1525, flag
