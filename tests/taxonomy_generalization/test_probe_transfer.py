"""v5.2 — safe-probe transfer audit."""
from __future__ import annotations

from desi.methodology_transfer.probe_generator import (
    probe_fires,
)
from desi.taxonomy_generalization.classifier import (
    classify_all,
)
from desi.taxonomy_generalization.corpus import all_chains
from desi.taxonomy_generalization.probe_transfer import (
    SAFE_PROBE_CLASSES, audit_probe_transfer,
    summarise_probe_transfer,
)


def test_six_safe_probe_classes() -> None:
    assert len(SAFE_PROBE_CLASSES) == 6


def test_safe_probe_set_matches_v50_safe_probes() -> None:
    expected = {
        "MT_MODAL_ASYMMETRY", "MT_NEGATION_ASYMMETRY",
        "MT_UNIVERSAL_LEAP", "MT_OVERLAP_LOOP",
        "MT_AUDIT_OVER_SUPPORT", "MT_AUDIT_OVER_BLOCK",
    }
    assert set(SAFE_PROBE_CLASSES) == expected


def test_safe_probe_false_activation_is_zero() -> None:
    chains = all_chains()
    results = classify_all(chains)
    outcomes = audit_probe_transfer(chains, results)
    _, false_act = summarise_probe_transfer(outcomes)
    assert false_act == 0


def test_safe_probe_hit_rate_meets_threshold() -> None:
    chains = all_chains()
    results = classify_all(chains)
    outcomes = audit_probe_transfer(chains, results)
    hit_rate, _ = summarise_probe_transfer(outcomes)
    assert hit_rate >= 0.80


def test_outcomes_cover_all_safe_probe_classes() -> None:
    chains = all_chains()
    results = classify_all(chains)
    outcomes = audit_probe_transfer(chains, results)
    names = {o.cluster_name for o in outcomes}
    assert names == set(SAFE_PROBE_CLASSES)


def test_no_safe_probe_fires_on_any_valid_chain() -> None:
    """Direct check: every safe probe should refuse to
    fire on every VALID chain in the v5.2 corpus."""
    valid = [c for c in all_chains() if c.ground_truth == "VALID"]
    for cluster in SAFE_PROBE_CLASSES:
        for c in valid:
            assert not probe_fires(cluster, c.text), (
                cluster, c.chain_id,
            )
