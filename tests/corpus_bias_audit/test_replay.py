"""v5.3 — counterfactual replay on RAW corpus."""
from __future__ import annotations

from desi.corpus_bias_audit.replay import (
    compute_rewrite_influence, replay_final, replay_raw,
)


def test_raw_replay_returns_outcome() -> None:
    r = replay_raw()
    assert r.corpus_label == "RAW"
    assert 0.0 <= r.taxonomy_coverage <= 1.0
    assert 0.0 <= r.probe_transfer_rate <= 1.0


def test_final_replay_returns_outcome() -> None:
    r = replay_final()
    assert r.corpus_label == "FINAL"
    assert r.safe_probe_false_activation == 0


def test_replay_is_deterministic() -> None:
    a = replay_raw().to_dict()
    b = replay_raw().to_dict()
    assert a == b


def test_rewrite_influence_quantifies_gains() -> None:
    raw = replay_raw()
    final = replay_final()
    inf = compute_rewrite_influence(raw, final)
    # Influence is just final - raw, by construction.
    assert inf.coverage_gain_from_rewrites == round(
        final.taxonomy_coverage - raw.taxonomy_coverage, 6,
    )
    assert inf.probe_gain_from_rewrites == round(
        final.probe_transfer_rate
        - raw.probe_transfer_rate, 6,
    )
    assert inf.false_activation_reduction == (
        raw.safe_probe_false_activation
        - final.safe_probe_false_activation
    )


def test_raw_replay_exposes_hidden_probe_activations() -> None:
    """v5.3's central finding: the RAW corpus carries
    safe-probe false activations that the v5.2 rewrites
    hid. If this regresses to 0, the audit lost its
    discriminating signal."""
    assert replay_raw().safe_probe_false_activation > 0
