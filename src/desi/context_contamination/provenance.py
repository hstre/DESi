"""Routing-provenance + effect analysis for the temperature comparison.

This module answers, deterministically and offline, the two questions the
provider-routing confound forced on the temperature study:

1. **Did the provider pin actually hold?** OpenRouter accepts a provider pin
   but the *served* backend (and its quantization) is only knowable after the
   fact. ``routing_provenance`` walks every per-call ``provider_sequence`` /
   ``served_model_sequence`` recorded by the runner and reports the distinct
   providers, distinct served models, and any *within-run* switching — the
   confound that makes a temperature contrast uninterpretable when it is
   present.

2. **Does an effect survive pinning?** ``hygiene_effect`` extracts the
   hygiene-minus-baseline effect for one case/metric at each temperature from a
   ``run_temperature_comparison`` report, and ``compare_reports`` puts a pinned
   and an unpinned report side by side. It reports the numbers and conservative
   sign/magnitude facts only — it attaches **no verdict**. Whether a halved
   effect "survived" is a judgement for the reader, not a threshold baked in
   here (consistent with the metrics module, which also refuses to verdict).

Everything here is pure stdlib and consumes only the JSON the workflow already
uploads — no network, no key, no model.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

DEFAULT_CASE = "advText3"
DEFAULT_METRIC = "framing_leakage"


def iter_run_results(obj: object) -> Iterator[dict]:
    """Yield every ``run_case`` result dict found anywhere in a report.

    A run result is identified structurally: a dict carrying both
    ``provider_sequence`` and ``case_id``. This walks comparison reports,
    factorial reports, density sweeps and plain benchmarks alike, so the
    provenance audit does not depend on the report's top-level shape.
    """
    if isinstance(obj, dict):
        if "provider_sequence" in obj and "case_id" in obj:
            yield obj
        else:
            for value in obj.values():
                yield from iter_run_results(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_run_results(value)


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def routing_provenance(report: dict, expected_provider: str | None = None) -> dict:
    """Provider / served-model distribution and pin-integrity flags.

    Counts are over individual upstream calls (``provider_sequence`` entries),
    not runs — a single run can switch provider mid-conversation, which is the
    failure this is built to surface. ``within_run_provider_switching`` /
    ``within_run_quantization_switching`` count the runs where that happened.

    When ``expected_provider`` is given (case-insensitive substring match
    against each reported provider name), ``provider_pin_clean`` is True only
    when every call landed on that provider and no run switched provider.
    """
    runs = list(iter_run_results(report))
    provider_calls: Counter[str] = Counter()
    served_calls: Counter[str] = Counter()
    provider_switching = 0
    quant_switching = 0

    for run in runs:
        provs = [p for p in run.get("provider_sequence", []) if p]
        served = [m for m in run.get("served_model_sequence", []) if m]
        provider_calls.update(provs)
        served_calls.update(served)
        if len(set(provs)) > 1:
            provider_switching += 1
        if len(set(served)) > 1:
            quant_switching += 1

    distinct_providers = sorted(provider_calls)
    distinct_served = sorted(served_calls)
    out: dict = {
        "n_runs": len(runs),
        "n_provider_calls": sum(provider_calls.values()),
        "provider_calls": dict(provider_calls),
        "served_model_calls": dict(served_calls),
        "distinct_providers": distinct_providers,
        "distinct_served_models": distinct_served,
        "within_run_provider_switching": provider_switching,
        "within_run_quantization_switching": quant_switching,
        "single_provider": len(distinct_providers) <= 1,
        "single_served_model": len(distinct_served) <= 1,
    }
    if expected_provider is not None:
        needle = expected_provider.lower()
        unexpected = sorted(p for p in distinct_providers if needle not in p.lower())
        out["expected_provider"] = expected_provider
        out["unexpected_providers"] = unexpected
        out["provider_pin_clean"] = (
            not unexpected and out["single_provider"] and provider_switching == 0
        )
    return out


def hygiene_effect(report: dict, case_id: str = DEFAULT_CASE,
                   metric: str = DEFAULT_METRIC) -> dict:
    """The hygiene-minus-baseline effect for one case/metric at each temperature.

    Reads a ``run_temperature_comparison`` report. The effect is negative when
    hygiene reduced the (contamination) metric relative to baseline.
    """
    effect = report["comparison"][metric]["hygiene_effect"][case_id]
    temps = [str(t) for t in report["temperatures"]]
    return {
        "case_id": case_id,
        "metric": metric,
        "temperatures": list(report["temperatures"]),
        "effect": {t: effect[t] for t in temps},
        "direction_changed": effect["direction_changed"],
    }


def compare_reports(pinned: dict, unpinned: dict, case_id: str = DEFAULT_CASE,
                    metric: str = DEFAULT_METRIC) -> dict:
    """Pinned vs unpinned hygiene effect for one case/metric — facts, no verdict.

    Both reports must share their two temperatures. For each temperature it
    reports the pinned and unpinned effect, whether the sign was preserved, the
    pinned-minus-unpinned difference, and (when the unpinned effect is non-zero)
    the magnitude ratio ``pinned / unpinned``. A ratio near 1 means pinning left
    the effect intact; near 0 means it collapsed; the reader decides what counts
    as "survived".
    """
    pe = hygiene_effect(pinned, case_id, metric)
    ue = hygiene_effect(unpinned, case_id, metric)
    if pe["temperatures"] != ue["temperatures"]:
        raise ValueError(
            f"temperature grids differ: pinned {pe['temperatures']} "
            f"vs unpinned {ue['temperatures']}"
        )

    per_temp: dict[str, dict] = {}
    for t in (str(x) for x in pe["temperatures"]):
        p_val = pe["effect"][t]
        u_val = ue["effect"][t]
        cell = {
            "pinned": p_val,
            "unpinned": u_val,
            "pinned_minus_unpinned": round(p_val - u_val, 4),
            "sign_preserved": _sign(p_val) == _sign(u_val),
        }
        if u_val != 0:
            cell["magnitude_ratio_pinned_over_unpinned"] = round(p_val / u_val, 4)
        per_temp[t] = cell

    return {
        "case_id": case_id,
        "metric": metric,
        "temperatures": pe["temperatures"],
        "pinned_effect": pe["effect"],
        "unpinned_effect": ue["effect"],
        "pinned_direction_changed": pe["direction_changed"],
        "unpinned_direction_changed": ue["direction_changed"],
        "per_temperature": per_temp,
    }


def summarize(report: dict, *, expected_provider: str | None = None,
              case_id: str = DEFAULT_CASE, metric: str = DEFAULT_METRIC) -> dict:
    """Routing provenance + the case/metric hygiene effect for one report."""
    out: dict = {"routing": routing_provenance(report, expected_provider)}
    try:
        out["hygiene_effect"] = hygiene_effect(report, case_id, metric)
    except (KeyError, TypeError):
        out["hygiene_effect"] = None  # not a temperature-comparison report
    return out


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Routing-provenance + hygiene-effect analysis for the "
                    "context-contamination temperature comparison (offline).")
    ap.add_argument("report", help="temperature-comparison report JSON (pinned run)")
    ap.add_argument("unpinned", nargs="?",
                    help="optional second report to compare against (unpinned run)")
    ap.add_argument("--provider", default=None,
                    help="expected pinned provider, e.g. Groq (checks the pin held)")
    ap.add_argument("--case", default=DEFAULT_CASE, help="case id (default advText3)")
    ap.add_argument("--metric", default=DEFAULT_METRIC,
                    help="metric (default framing_leakage)")
    args = ap.parse_args(argv)

    report = _load(args.report)
    result = summarize(report, expected_provider=args.provider,
                       case_id=args.case, metric=args.metric)
    if args.unpinned:
        result["pinned_vs_unpinned"] = compare_reports(
            report, _load(args.unpinned), args.case, args.metric)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
