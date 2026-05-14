"""Tests for v0.9 PathQualityMetrics signature fields.

The three new fields ``unique_claim_order_hash``,
``branch_signature`` and ``merge_signature`` let two runs over the
same scenario be compared by *path*, not just by count. v0.9 needs
these so that the multi-seed report's ``unique_path_count`` is a
function of actual behaviour, not just of counter values.
"""
from __future__ import annotations

from desi.eval import EvaluationHarness, SeededScenarioEngine, scenario_by_id
from desi.evolution import compute_path_quality
from desi.evolution.paired_evaluation import _ConfiguredHarness


# ---------------------------------------------------------------------------
# Default-construction backwards-compat: v0.8 callers still work.
# ---------------------------------------------------------------------------


def test_path_quality_metrics_accepts_minimal_kwargs() -> None:
    from desi.evolution import PathQualityMetrics
    m = PathQualityMetrics(
        scenario_id="S2", timeline_length=25, branch_opened_count=3,
        guard_blocked_count=0, contradicts_count=2, merged_into_count=0,
        hook_error_count=0,
    )
    # Signature fields default to empty string — no need for v0.8 callers
    # to pass them.
    assert m.unique_claim_order_hash == ""
    assert m.branch_signature == ""
    assert m.merge_signature == ""


# ---------------------------------------------------------------------------
# Computed signatures are non-empty for real runs.
# ---------------------------------------------------------------------------


def _run_static(scenario_id: str, seed: int = 42):
    harness = EvaluationHarness(model="deterministic")
    return compute_path_quality(
        harness.run_scenario(scenario_by_id(scenario_id), seed=seed)
    )


def test_static_run_produces_non_empty_signatures() -> None:
    m = _run_static("S2")
    assert m.unique_claim_order_hash != ""
    assert m.branch_signature != ""
    assert m.merge_signature != ""


# ---------------------------------------------------------------------------
# Two seed-variants produce different branch_signatures on the
# variant scenario.
# ---------------------------------------------------------------------------


def _run_seeded(scenario_id: str, seed: int, *, config: dict | None = None):
    engine = SeededScenarioEngine()
    inst = engine.instantiate(scenario_id, seed)
    harness = _ConfiguredHarness(
        model="deterministic", seed=seed, config=config or {},
    )
    return compute_path_quality(harness.run_scenario(inst))


def test_branch_signature_differs_across_seeds_on_variant_scenario() -> None:
    m42 = _run_seeded("ADV_BRANCH_EXPLOSION", 42)
    m43 = _run_seeded("ADV_BRANCH_EXPLOSION", 43)
    assert m42.branch_signature != m43.branch_signature


def test_claim_order_hash_differs_across_seeds_on_variant_scenario() -> None:
    m42 = _run_seeded("ADV_BRANCH_EXPLOSION", 42)
    m43 = _run_seeded("ADV_BRANCH_EXPLOSION", 43)
    assert m42.unique_claim_order_hash != m43.unique_claim_order_hash


def test_static_scenario_signature_is_stable_across_seeds() -> None:
    """S5 has no variant generator; signatures should match across
    seeds because the trajectory is identical."""
    m42 = _run_seeded("S5", 42)
    m43 = _run_seeded("S5", 43)
    assert m42.branch_signature == m43.branch_signature


def test_same_seed_same_signature_is_idempotent() -> None:
    a = _run_seeded("ADV_BRANCH_EXPLOSION", 42)
    b = _run_seeded("ADV_BRANCH_EXPLOSION", 42)
    assert a.branch_signature == b.branch_signature
    assert a.unique_claim_order_hash == b.unique_claim_order_hash


# ---------------------------------------------------------------------------
# Signatures are short stable hashes
# ---------------------------------------------------------------------------


def test_signatures_are_16_char_hex() -> None:
    m = _run_static("S2")
    for sig in (m.unique_claim_order_hash, m.branch_signature,
                m.merge_signature):
        assert len(sig) == 16
        assert all(c in "0123456789abcdef" for c in sig)


# ---------------------------------------------------------------------------
# to_dict() carries the new fields
# ---------------------------------------------------------------------------


def test_to_dict_includes_signatures() -> None:
    m = _run_static("S2")
    d = m.to_dict()
    for k in ("unique_claim_order_hash", "branch_signature",
              "merge_signature"):
        assert k in d
        assert d[k] != ""
