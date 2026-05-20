"""Aufgabe 8 — contamination probe against six protected pools."""
from __future__ import annotations

from desi.frame_consistency_probe.contamination import probe_contamination


def test_probe_covers_six_pools() -> None:
    r = probe_contamination()
    assert r.checked_pool_count == 6
    # Per-pool hit map enumerates every pool, even those with 0 hits.
    assert set(r.per_pool_hits) == {
        "v1_5_main",
        "v1_9_tools",
        "v2_3_multistep",
        "v3_4_frame",
        "v3_5_invariance",
        "v3_8_context_probe",
    }


def test_contamination_risk_is_zero() -> None:
    r = probe_contamination()
    assert r.contamination_risk == 0.0, (
        f"contamination_risk={r.contamination_risk}, "
        f"hits: {[h.to_dict() for h in r.hits]}"
    )


def test_no_hits_recorded() -> None:
    r = probe_contamination()
    assert len(r.hits) == 0


def test_introduced_count_includes_manipulation_and_synthetic_corpus() -> None:
    # 20 manipulation fixtures + ≥ 5 synthetic GROUP_C bare sentences
    # × 5 outer frames = at minimum 45 introduced sentences.
    r = probe_contamination()
    assert r.introduced_count >= 45


def test_probe_is_deterministic() -> None:
    a = probe_contamination()
    b = probe_contamination()
    assert a.to_dict() == b.to_dict()
