"""Tests for v2.6 probe metrics (Aufgabe 6)."""
from __future__ import annotations

from desi.causal_probe import (
    CausalChainProbeRunner,
    RiskFlag,
    compute_probe_metrics,
)


def test_metrics_carry_required_observables() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    for f in (
        "multistep_trigger_rate", "main_trigger_rate",
        "known_false_positive_reopen_rate", "authority_touch_rate",
        "philosophy_touch_rate", "metaphor_touch_rate",
        "safe_candidate_rate",
    ):
        assert hasattr(m, f)


def test_rates_are_in_unit_interval() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    for r in (
        m.multistep_trigger_rate, m.main_trigger_rate,
        m.known_false_positive_reopen_rate, m.authority_touch_rate,
        m.philosophy_touch_rate, m.metaphor_touch_rate,
        m.safe_candidate_rate,
    ):
        assert 0.0 <= r <= 1.0


def test_total_is_eighty() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    assert m.total == 80


def test_triggered_subsets_add_up() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    assert (m.triggered_multistep + m.triggered_main
            == m.triggered_total)


def test_metrics_are_deterministic() -> None:
    a = compute_probe_metrics(CausalChainProbeRunner().run())
    b = compute_probe_metrics(CausalChainProbeRunner().run())
    assert a.to_dict() == b.to_dict()


def test_risk_flag_distribution_uses_closed_enum_keys() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    closed = {f.value for f in RiskFlag}
    assert set(m.risk_flag_distribution.keys()) == closed


def test_per_category_trigger_covers_a_through_e_and_r1_through_r5() -> None:
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    expected = {
        "main_50:A", "main_50:B", "main_50:C", "main_50:D", "main_50:E",
        "multistep_30:R1", "multistep_30:R2", "multistep_30:R3",
        "multistep_30:R4", "multistep_30:R5",
    }
    assert set(m.per_category_trigger.keys()) == expected


def test_no_known_false_positive_reopen_on_current_data() -> None:
    """The probe's empirical claim: with the directive-mandated
    trigger shape, none of the 8 known FPs are matched."""
    m = compute_probe_metrics(CausalChainProbeRunner().run())
    assert m.triggered_known_false_positives == 0
    assert m.known_false_positive_reopen_rate == 0.0
