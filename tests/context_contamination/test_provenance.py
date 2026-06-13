"""Routing-provenance + hygiene-effect analysis (offline, no network).

Synthetic reports stand in for the workflow's JSON so the pin-integrity audit
and the pinned-vs-unpinned effect comparison are exercised without a live run.
"""
from __future__ import annotations

import json

import pytest

from desi.context_contamination import (
    compare_reports,
    hygiene_effect,
    iter_run_results,
    routing_provenance,
    summarize,
)
from desi.context_contamination.provenance import main


def _run(case_id, provider_seq, served_seq=None):
    """Minimal run_case-shaped result for the provenance walker."""
    return {
        "case_id": case_id,
        "provider_sequence": list(provider_seq),
        "served_model_sequence": list(served_seq or [None] * len(provider_seq)),
    }


def _temp_report(effect_low, effect_high, *, runs, temps=(0.0, 0.7),
                 metric="framing_leakage"):
    """A run_temperature_comparison-shaped report with one case effect + runs."""
    lo, hi = (str(t) for t in temps)
    sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
    return {
        "temperatures": list(temps),
        "comparison": {
            metric: {
                "hygiene_effect": {
                    "advText3": {
                        lo: effect_low, hi: effect_high,
                        "direction_changed": sign(effect_low) != sign(effect_high),
                    }
                }
            }
        },
        "per_temperature": {
            lo: {"reports": [{"runs": {"baseline": {}, "desi_hygiene": {}}}]},
            hi: {"reports": [{"runs": runs}]},
        },
    }


# --- iter_run_results -----------------------------------------------------------

def test_iter_run_results_finds_nested_runs_and_skips_non_runs():
    report = {
        "comparison": {"framing_leakage": {"hygiene_effect": {"advText3": {}}}},
        "per_temperature": {
            "0.0": {"reports": [{"runs": {
                "baseline": _run("advText3", ["Groq"]),
                "desi_hygiene": _run("advText5", ["Groq"]),
            }}]},
        },
    }
    found = list(iter_run_results(report))
    assert {r["case_id"] for r in found} == {"advText3", "advText5"}
    # the hygiene_effect dict has no provider_sequence -> not mistaken for a run
    assert all("provider_sequence" in r for r in found)


# --- routing_provenance ---------------------------------------------------------

def test_routing_provenance_counts_calls_and_distinct_providers():
    report = {"x": [_run("c1", ["Groq", "Groq", "Novita"]),
                    _run("c2", ["Groq", "Groq"])]}
    prov = routing_provenance(report)
    assert prov["n_runs"] == 2
    assert prov["n_provider_calls"] == 5
    assert prov["provider_calls"] == {"Groq": 4, "Novita": 1}
    assert prov["distinct_providers"] == ["Groq", "Novita"]
    assert prov["within_run_provider_switching"] == 1   # only c1 switched
    assert prov["single_provider"] is False


def test_routing_provenance_clean_pin():
    report = {"x": [_run("c1", ["Groq", "Groq"], ["m:fp8", "m:fp8"]),
                    _run("c2", ["Groq", "Groq"], ["m:fp8", "m:fp8"])]}
    prov = routing_provenance(report, expected_provider="Groq")
    assert prov["single_provider"] is True
    assert prov["single_served_model"] is True
    assert prov["unexpected_providers"] == []
    assert prov["provider_pin_clean"] is True


def test_routing_provenance_detects_unexpected_provider_and_quant_switch():
    report = {"x": [_run("c1", ["Groq", "DeepInfra"], ["m:fp8", "m:fp16"])]}
    prov = routing_provenance(report, expected_provider="Groq")
    assert prov["unexpected_providers"] == ["DeepInfra"]
    assert prov["provider_pin_clean"] is False
    assert prov["within_run_quantization_switching"] == 1
    assert prov["single_served_model"] is False


def test_routing_provenance_pin_clean_false_when_within_run_switch_only():
    # all calls are Groq, but one run switched provider mid-run is impossible
    # here; instead a served-model switch must NOT flip provider_pin_clean,
    # while a provider switch must.
    switched = {"x": [_run("c1", ["Groq", "groq-2"])]}  # two provider names
    prov = routing_provenance(switched, expected_provider="Groq")
    assert prov["within_run_provider_switching"] == 1
    assert prov["provider_pin_clean"] is False


# --- hygiene_effect -------------------------------------------------------------

def test_hygiene_effect_extracts_per_temperature_effect():
    report = _temp_report(-5.6, -2.8, runs={"baseline": {}, "desi_hygiene": {}})
    eff = hygiene_effect(report)
    assert eff["case_id"] == "advText3"
    assert eff["metric"] == "framing_leakage"
    assert eff["effect"] == {"0.0": -5.6, "0.7": -2.8}
    assert eff["direction_changed"] is False   # both negative


# --- compare_reports ------------------------------------------------------------

def test_compare_reports_pinned_vs_unpinned_facts():
    runs = {"baseline": _run("advText3", ["Groq"]),
            "desi_hygiene": _run("advText3", ["Groq"])}
    pinned = _temp_report(-5.4, -5.0, runs=runs)       # effect survives pinning
    unpinned = _temp_report(-5.6, -2.8, runs=runs)     # the observed confounded run
    cmp = compare_reports(pinned, unpinned)
    assert cmp["temperatures"] == [0.0, 0.7]
    low = cmp["per_temperature"]["0.0"]
    assert low["pinned"] == -5.4 and low["unpinned"] == -5.6
    assert low["sign_preserved"] is True
    assert low["magnitude_ratio_pinned_over_unpinned"] == round(-5.4 / -5.6, 4)
    high = cmp["per_temperature"]["0.7"]
    # pinned keeps the strong effect; unpinned had halved it
    assert high["pinned_minus_unpinned"] == round(-5.0 - -2.8, 4)


def test_compare_reports_rejects_mismatched_temperature_grids():
    runs = {"baseline": {}, "desi_hygiene": {}}
    a = _temp_report(-1.0, -1.0, runs=runs, temps=(0.0, 0.7))
    b = _temp_report(-1.0, -1.0, runs=runs, temps=(0.0, 1.0))
    with pytest.raises(ValueError, match="temperature grids differ"):
        compare_reports(a, b)


def test_compare_reports_zero_unpinned_has_no_ratio():
    runs = {"baseline": {}, "desi_hygiene": {}}
    pinned = _temp_report(-2.0, -2.0, runs=runs)
    unpinned = _temp_report(0.0, -2.0, runs=runs)
    cmp = compare_reports(pinned, unpinned)
    assert "magnitude_ratio_pinned_over_unpinned" not in cmp["per_temperature"]["0.0"]
    assert cmp["per_temperature"]["0.0"]["sign_preserved"] is False  # 0 vs -2


# --- summarize + CLI ------------------------------------------------------------

def test_summarize_bundles_routing_and_effect():
    runs = {"baseline": _run("advText3", ["Groq"]),
            "desi_hygiene": _run("advText3", ["Groq"])}
    report = _temp_report(-3.0, -1.0, runs=runs)
    out = summarize(report, expected_provider="Groq")
    assert out["routing"]["provider_pin_clean"] is True
    assert out["hygiene_effect"]["effect"] == {"0.0": -3.0, "0.7": -1.0}


def test_summarize_handles_non_comparison_report():
    # a plain routing-only blob: no comparison key -> hygiene_effect is None
    report = {"runs": {"baseline": _run("advText3", ["Groq"])}}
    out = summarize(report)
    assert out["hygiene_effect"] is None
    assert out["routing"]["distinct_providers"] == ["Groq"]


def test_cli_main_emits_json_with_comparison(tmp_path, capsys):
    runs = {"baseline": _run("advText3", ["Groq", "Groq"]),
            "desi_hygiene": _run("advText3", ["Groq", "Groq"])}
    pinned = tmp_path / "pinned.json"
    unpinned = tmp_path / "unpinned.json"
    pinned.write_text(json.dumps(_temp_report(-5.4, -5.0, runs=runs)))
    unpinned.write_text(json.dumps(_temp_report(-5.6, -2.8, runs=runs)))

    rc = main([str(pinned), str(unpinned), "--provider", "Groq"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["routing"]["provider_pin_clean"] is True
    assert payload["pinned_vs_unpinned"]["per_temperature"]["0.7"]["pinned"] == -5.0
