"""v5.3 — bias metrics."""
from __future__ import annotations

from desi.corpus_bias_audit.bias_metrics import (
    compute_bias_metrics,
)
from desi.corpus_bias_audit.diff import audit_pair
from desi.corpus_bias_audit.raw_corpus import all_pairs


def _metrics():
    audits = tuple(audit_pair(p) for p in all_pairs())
    return compute_bias_metrics(audits)


def test_metrics_keys_are_six() -> None:
    m = _metrics().to_dict()
    assert len(m) == 6


def test_all_metric_values_nonnegative() -> None:
    m = _metrics().to_dict()
    for v in m.values():
        assert v >= 0.0


def test_rewrite_fraction_in_unit_interval() -> None:
    m = _metrics()
    assert 0.0 <= m.rewrite_fraction <= 1.0


def test_semantic_shift_max_geq_mean() -> None:
    m = _metrics()
    assert m.semantic_shift_max >= m.semantic_shift_mean


def test_metrics_deterministic() -> None:
    a = _metrics().to_dict()
    b = _metrics().to_dict()
    assert a == b


def test_metrics_reflect_known_bias_in_v52_corpus() -> None:
    """v5.2 had heavy rewrites; the audit should surface
    this — i.e. rewrite_fraction is materially above 0
    (the threshold of 0.25 is intentionally exceeded
    because v5.2 actually did engineer the corpus to
    fit the probes)."""
    m = _metrics()
    assert m.rewrite_fraction > 0.0
    # Either valid_probe_avoidance_rate or
    # invalid_probe_alignment_rate must reflect the
    # known engineering bias in v5.2.
    assert (
        m.valid_probe_avoidance_rate > 0.0
        or m.invalid_probe_alignment_rate > 0.0
    )
