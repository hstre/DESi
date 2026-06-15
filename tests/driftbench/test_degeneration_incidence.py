"""Reproduction test for the DriftBench degeneration-incidence metric.

Pins the pre-registered degeneration numbers to the committed dataset
``data/driftbench/driftbench_compression.jsonl`` so they are runnable, not
asserted. See ``scripts/degeneration_incidence.py`` for the pre-registration
and the scope caveats (this is state-representation degeneration, partly
entangled with compression, NOT the behavioural loop-trap metric).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from degeneration_incidence import (  # noqa: E402
    DATA,
    PRIMARY_TAU,
    compute,
    load,
    mcnemar_exact_p,
)


@pytest.fixture(scope="module")
def stats() -> dict:
    assert DATA.exists(), f"dataset missing: {DATA}"
    return compute(load())


def test_paired_count(stats):
    assert stats["n"] == 1525


def test_primary_incidence(stats):
    p = stats["primary"]
    assert p["tau"] == PRIMARY_TAU
    # raw 74.4% degenerate -> DESi state 0.1%
    assert p["raw_count"] == 1135
    assert p["desi_count"] == 1
    assert round(p["raw_incidence"] * 100, 1) == 74.4
    assert round(p["desi_incidence"] * 100, 1) == 0.1


def test_primary_is_monotone_improvement(stats):
    # the layer never made a trajectory degenerate that the raw arm kept clean
    p = stats["primary"]
    assert p["pairs_layer_broke"] == 0
    assert p["pairs_layer_fixed"] == 1134


def test_primary_significant(stats):
    # well powered at n=1525 (paired); a null here would be informative
    assert stats["primary"]["mcnemar_p"] < 1e-50


def test_sensitivity_directionally_stable(stats):
    # across every pre-registered threshold the layer reduces incidence and
    # never increases it (pairs_layer_broke == 0 throughout)
    taus = [row["tau"] for row in stats["sensitivity"]]
    assert taus == [0.30, 0.40, 0.50, 0.60, 0.70]
    for row in stats["sensitivity"]:
        assert row["abs_reduction"] > 0
        assert row["pairs_layer_broke"] == 0


def test_hard_lock_in_subset(stats):
    # the categorical loop-trap analog: 47 trajectories, all degenerate raw,
    # none degenerate in the DESi state
    assert stats["hard_lock_in_n"] == 47
    lock = stats["hard_lock_in"]
    assert lock["raw_count"] == 47
    assert lock["desi_count"] == 0


def test_single_shot_is_null_sanity_check(stats):
    # single_shot has no multi-turn drift to compress -> 0/0 in both arms.
    # this internal control guards against a metric that "wins" everywhere.
    ss = stats["by_condition"]["single_shot"]
    assert ss["raw_count"] == 0
    assert ss["desi_count"] == 0
    assert ss["mcnemar_p"] == 1.0


def test_preservation_flags_constant(stats):
    # all four are constant -> deliberately excluded from the metric
    assert all(stats["preservation_flags_constant"].values())


def test_mcnemar_helper():
    assert mcnemar_exact_p(0, 0) == 1.0
    assert mcnemar_exact_p(5, 5) == 1.0       # perfectly balanced -> p=1
    assert mcnemar_exact_p(10, 0) < 0.01      # all one-directional -> small p
