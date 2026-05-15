"""Tests for v2.6 RiskFlag enum + known-FP list (Aufgabe 5)."""
from __future__ import annotations

from desi.causal_probe import KNOWN_FALSE_POSITIVE_CASE_IDS, RiskFlag


_EXPECTED = {
    "would_reopen_known_false_positive",
    "would_touch_authority_case",
    "would_touch_philosophy_case",
    "would_touch_metaphor_case",
    "would_touch_everyday_causal_case",
    "would_touch_valid_multistep_case",
    "would_touch_cycle_case",
    "would_touch_contradiction_case",
    "no_risk_flag",
}


def test_nine_risk_flags_exactly() -> None:
    assert len(list(RiskFlag)) == 9


def test_risk_flag_set_matches_directive() -> None:
    assert {f.value for f in RiskFlag} == _EXPECTED


def test_each_directive_name_present() -> None:
    for name in (
        "WOULD_REOPEN_KNOWN_FALSE_POSITIVE",
        "WOULD_TOUCH_AUTHORITY_CASE",
        "WOULD_TOUCH_PHILOSOPHY_CASE",
        "WOULD_TOUCH_METAPHOR_CASE",
        "WOULD_TOUCH_EVERYDAY_CAUSAL_CASE",
        "WOULD_TOUCH_VALID_MULTISTEP_CASE",
        "WOULD_TOUCH_CYCLE_CASE",
        "WOULD_TOUCH_CONTRADICTION_CASE",
        "NO_RISK_FLAG",
    ):
        assert hasattr(RiskFlag, name), name


def test_known_false_positive_ids_match_directive() -> None:
    expected = {"A5", "A6", "A7", "A10", "D3", "E4", "E5", "E10"}
    assert KNOWN_FALSE_POSITIVE_CASE_IDS == expected
    assert len(KNOWN_FALSE_POSITIVE_CASE_IDS) == 8


def test_risk_flag_is_str_compatible() -> None:
    assert isinstance(RiskFlag.NO_RISK_FLAG.value, str)
