"""v5.4 — taxonomy/probe independence audit."""
from __future__ import annotations

from desi.raw_generalization.independence_audit import (
    audit_independence,
)
from desi.raw_generalization.probe_eval import (
    evaluate_probes,
)
from desi.raw_generalization.raw_corpus_loader import (
    load_raw_chains,
)
from desi.raw_generalization.taxonomy_eval import (
    evaluate_taxonomy,
)


def _audit():
    chains = load_raw_chains()
    tax, results = evaluate_taxonomy(chains)
    probe = evaluate_probes(chains, results)
    return audit_independence(
        tax, probe,
        taxonomy_thresholds_passed=True,
        probe_thresholds_passed=False,
    )


def test_correlation_in_unit_interval() -> None:
    c = _audit().taxonomy_probe_correlation
    assert -1.0 <= c <= 1.0


def test_taxonomy_survives_probe_failure_is_true() -> None:
    """Aufgabe 8 requirement: taxonomy metrics must
    remain valid even when probes fail."""
    assert _audit().taxonomy_survives_probe_failure is True


def test_audit_serializable() -> None:
    d = _audit().to_dict()
    assert "taxonomy_probe_correlation" in d
    assert "taxonomy_survives_probe_failure" in d
