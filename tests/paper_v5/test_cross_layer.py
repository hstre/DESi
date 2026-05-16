"""v5.5 — cross-layer claims explicitly encoded."""
from __future__ import annotations

from ._helpers import load_claims


def test_cross_layer_claim_for_diagnostic_does_not_imply_intervention() -> None:
    """At least one explicit cross_layer claim states
    that diagnostic transfer does not imply intervention
    transfer."""
    crosses = [
        c for c in load_claims()
        if c["claim_scope"] == "cross_layer"
    ]
    assert any(
        "diagnostic transfer does NOT imply intervention"
        in c["text"]
        for c in crosses
    )


def test_cross_layer_claim_links_rewrites_to_probe_gain() -> None:
    crosses = [
        c for c in load_claims()
        if c["claim_scope"] == "cross_layer"
    ]
    assert any(
        "corpus rewrites carry probe-transfer claim" in c["text"]
        for c in crosses
    )


def test_cross_layer_claim_links_rewrites_to_zero_coverage_gain() -> None:
    crosses = [
        c for c in load_claims()
        if c["claim_scope"] == "cross_layer"
    ]
    assert any(
        "corpus rewrites do NOT carry taxonomy coverage"
        in c["text"]
        for c in crosses
    )


def test_cross_layer_claim_records_false_activation_on_raw() -> None:
    crosses = [
        c for c in load_claims()
        if c["claim_scope"] == "cross_layer"
    ]
    assert any(
        "false-activate 192 times" in c["text"]
        for c in crosses
    )


def test_cross_layer_claim_states_taxonomy_independence() -> None:
    crosses = [
        c for c in load_claims()
        if c["claim_scope"] == "cross_layer"
    ]
    assert any(
        "taxonomy is independently evaluable" in c["text"]
        for c in crosses
    )
