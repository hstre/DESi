"""Aufgabe 7 — contamination probe over the five protected pools."""
from __future__ import annotations

from desi.frame_context_probe.contamination import (
    ContaminationResult,
    aggregate_contamination,
    probe_all_fixtures,
)


_REQUIRED_POOLS = {
    "v1_5_main",
    "v1_9_tools",
    "v2_3_multistep",
    "v3_4_frame",
    "v3_5_invariance",
}


def test_probe_returns_results_for_every_fixture_phrase() -> None:
    results = probe_all_fixtures()
    # 10 explicit-frame + 9 section + 38 domain-token phrases.
    assert len(results) >= 50


def test_each_result_covers_all_five_pools() -> None:
    for r in probe_all_fixtures():
        assert isinstance(r, ContaminationResult)
        assert set(r.per_benchmark_hits) == _REQUIRED_POOLS


def test_section_header_phrases_are_zero_risk() -> None:
    # The literal "Section: ..." prefix is unique to our fixtures and
    # must not appear in any protected benchmark text.
    for r in probe_all_fixtures():
        if r.signal == "section_header":
            assert r.contamination_risk == 0.0, (
                f"section header phrase leaked into protected pools: "
                f"{r.phrase!r} hits={r.per_benchmark_hits}"
            )


def test_explicit_frame_marker_leaks_into_v34_and_v35() -> None:
    # v3.4 cases and v3.5 invariance paraphrases both ship
    # ``Frame: <name>`` prefixes — so the explicit-frame phrases
    # *must* show non-zero contamination. If this test fails the
    # benchmark texts have changed and the report's "contamination"
    # finding would silently become a false negative.
    explicit_hits = [
        r for r in probe_all_fixtures()
        if r.signal == "explicit_frame" and r.contamination_risk > 0.0
    ]
    assert explicit_hits, (
        "no explicit-frame phrase matched a protected pool; the "
        "contamination probe is no longer meaningful"
    )


def test_aggregate_contamination_shape() -> None:
    summary = aggregate_contamination(probe_all_fixtures())
    for key in (
        "total_phrases",
        "zero_risk_phrases",
        "nonzero_risk_phrases",
        "max_contamination_risk",
        "by_signal",
    ):
        assert key in summary
    assert summary["total_phrases"] == (
        summary["zero_risk_phrases"] + summary["nonzero_risk_phrases"]
    )


def test_probe_is_deterministic_across_runs() -> None:
    a = probe_all_fixtures()
    b = probe_all_fixtures()
    assert [r.to_dict() for r in a] == [r.to_dict() for r in b]
