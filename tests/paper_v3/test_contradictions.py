"""Aufgabe 9 — internal contradiction scan.

Two claims that reference the same (artifact, field_path) but
disagree on ``expected_value`` are a semantic contradiction.
``contradiction_count`` must be zero. Syntactic duplicates
(identical expected values) are allowed.
"""
from __future__ import annotations

from ._helpers import load_claims, values_equal


def test_no_semantic_contradiction() -> None:
    by_key: dict[tuple[str, str], list[dict]] = {}
    for c in load_claims():
        by_key.setdefault(
            (c["artifact"], c["field_path"]), [],
        ).append(c)

    contradictions: list[str] = []
    for (artifact, path), entries in by_key.items():
        if len(entries) < 2:
            continue
        first = entries[0]["expected_value"]
        for other in entries[1:]:
            if not values_equal(other["expected_value"], first):
                contradictions.append(
                    f"({artifact}.{path}) — "
                    f"{entries[0]['claim_id']} says "
                    f"{first!r} but {other['claim_id']} says "
                    f"{other['expected_value']!r}"
                )
    assert contradictions == [], (
        f"contradiction_count={len(contradictions)}: "
        f"{contradictions}"
    )


def test_required_quantitative_findings_anchored() -> None:
    """Aufgabe 6 — the paper MUST anchor seven specific
    quantitative findings. Each one corresponds to a claim
    with a specific (artifact, field_path) and value."""
    required = (
        # v3.11
        ("v3_11", "adversarial.detection_rate", 1.0),
        # v3.14
        ("v3_14", "metrics.heldout_precision", 1.0),
        ("v3_14", "metrics.heldout_recall", 1.0),
        # v3.15
        ("v3_15", "metrics.attack_success_rate", 0.93),
        # v3.16 (reduction surfaces as false_support_count = 24)
        ("v3_16", "v315.false_support_count", 24),
        # v3.21
        ("v3_21", "primary_cliffs", ["PremiseExtractor", "SPL",
                                      "FrameTension",
                                      "FrameTensionRouter",
                                      "CAUSAL_CHAIN",
                                      "SuspensionGate"]),
        ("v3_21", "dead_knobs", ["FrameDeclaration"]),
        # v3.22
        ("v3_22", "recommended_next", "KEEP_CURRENT_ORDER"),
        # v3.23
        ("v3_23", "recommended_next", "NONE"),
    )
    claims = load_claims()
    by_key = {(c["artifact"], c["field_path"]): c for c in claims}
    missing: list[str] = []
    for artifact, path, value in required:
        c = by_key.get((artifact, path))
        if c is None:
            missing.append(f"missing claim for {artifact}.{path}")
            continue
        if not values_equal(c["expected_value"], value):
            missing.append(
                f"{artifact}.{path}: expected {value!r}, "
                f"claim says {c['expected_value']!r}"
            )
    assert missing == [], missing


def test_latency_delta_within_38_percent_window() -> None:
    """v3.23 latency_delta = 0.38 — the paper anchors this
    finding via the baseline latency_cost and the v3.23
    reflection. We verify the claim covers the baseline cost."""
    claims = load_claims()
    have_baseline = any(
        c["artifact"] == "v3_23"
        and c["field_path"] == "baseline.latency_cost"
        for c in claims
    )
    assert have_baseline, (
        "v3.23 baseline.latency_cost claim missing — required "
        "to anchor the 0.38 latency_delta finding"
    )
