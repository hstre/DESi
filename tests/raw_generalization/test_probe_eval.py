"""v5.4 — probe-only metrics on RAW corpus."""
from __future__ import annotations

from desi.raw_generalization.probe_eval import (
    evaluate_probes,
)
from desi.raw_generalization.raw_corpus_loader import (
    load_raw_chains,
)
from desi.raw_generalization.report import (
    MAX_PROBE_DOMAIN_VARIANCE, MAX_PROBE_FALSE_ACTIVATION,
    MIN_PROBE_HIT_RATE,
)


def _probe_metrics():
    return evaluate_probes(load_raw_chains())


def test_channel_is_probe_only() -> None:
    assert _probe_metrics().channel == "probe_only"


def test_probes_fail_hit_rate_on_raw_corpus() -> None:
    """The whole point of v5.4: probes do not hit their
    threshold on the unedited corpus."""
    assert _probe_metrics().probe_hit_rate < (
        MIN_PROBE_HIT_RATE
    )


def test_probes_fail_false_activation_on_raw_corpus() -> None:
    """RAW corpus exposes hidden false activations on
    VALID chains."""
    assert _probe_metrics().probe_false_activation > (
        MAX_PROBE_FALSE_ACTIVATION
    )


def test_probe_domain_variance_meets_threshold() -> None:
    """Domain variance — a structural metric — should
    still pass."""
    assert _probe_metrics().probe_domain_variance <= (
        MAX_PROBE_DOMAIN_VARIANCE
    )


def test_probe_alignment_loss_matches_v52_to_raw_gap() -> None:
    """v5.2 FINAL hit_rate minus RAW hit_rate."""
    pm = _probe_metrics()
    assert pm.probe_alignment_loss > 0.0


def test_probe_outcomes_count_matches_six() -> None:
    pm = _probe_metrics()
    assert len(pm.outcomes) == 6


def test_probe_metrics_deterministic() -> None:
    a = _probe_metrics().to_dict()
    b = _probe_metrics().to_dict()
    assert a == b
