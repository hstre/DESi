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

from reproduce_driftbench import DATA, compute, load, steiger_z  # noqa: E402


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


def test_rho_is_not_significantly_different_from_one(stats):
    # README: Steiger's Z for the dependent correlations = 1.65, p = 0.098 —
    # rho's deviation from 1.0 is a point estimate, not a demonstrated gain.
    # Pinning this keeps the claim honest: if new data ever makes it
    # significant, this test fails and the README wording must be revisited.
    assert round(stats["steiger_z"], 2) == 1.65
    assert round(stats["steiger_p_two_sided"], 3) == 0.098
    assert stats["steiger_p_two_sided"] >= 0.05


# ---- steiger_z behavioural pins (validated against a paired bootstrap on the
# ---- real data: bootstrap z = 1.63 / p = 0.104 vs Steiger z = 1.65 / p = 0.099)

def test_steiger_zero_when_correlations_equal():
    z, p = steiger_z(0.5, 0.5, 0.3, 1000)
    assert z == 0.0 and p == 1.0


def test_steiger_sign_follows_argument_order():
    z_pos, _ = steiger_z(0.6, 0.4, 0.3, 500)
    z_neg, _ = steiger_z(0.4, 0.6, 0.3, 500)
    assert z_pos > 0 and z_neg < 0
    assert round(z_pos + z_neg, 12) == 0.0          # antisymmetric


def test_steiger_more_data_means_more_power():
    z_small, p_small = steiger_z(0.5, 0.4, 0.3, 50)
    z_large, p_large = steiger_z(0.5, 0.4, 0.3, 5000)
    assert abs(z_large) > abs(z_small)
    assert p_large < p_small


def test_steiger_higher_overlap_means_more_power():
    # the more the two predictors correlate, the more variance of the
    # difference cancels -> same delta becomes more significant
    _, p_lo = steiger_z(0.5, 0.4, 0.1, 500)
    _, p_hi = steiger_z(0.5, 0.4, 0.9, 500)
    assert p_hi < p_lo


def test_structural_preservation_flags(stats):
    # README: all four structural families preserved 1525/1525
    for flag, count in stats["preservation"].items():
        assert count == 1525, flag
