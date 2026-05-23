"""Causal-chain probe metrics — Aufgabe 6."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .pattern import BenchmarkSource
from .risk import KNOWN_FALSE_POSITIVE_CASE_IDS, RiskFlag
from .runner import CausalProbeRun


@dataclass(frozen=True)
class ProbeMetrics:
    total: int
    triggered_total: int
    triggered_multistep: int
    triggered_main: int
    triggered_known_false_positives: int
    multistep_trigger_rate: float
    main_trigger_rate: float
    known_false_positive_reopen_rate: float
    authority_touch_rate: float
    philosophy_touch_rate: float
    metaphor_touch_rate: float
    safe_candidate_rate: float
    risk_flag_distribution: dict[str, int]
    per_category_trigger: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "triggered_total": self.triggered_total,
            "triggered_multistep": self.triggered_multistep,
            "triggered_main": self.triggered_main,
            "triggered_known_false_positives":
                self.triggered_known_false_positives,
            "multistep_trigger_rate": self.multistep_trigger_rate,
            "main_trigger_rate": self.main_trigger_rate,
            "known_false_positive_reopen_rate":
                self.known_false_positive_reopen_rate,
            "authority_touch_rate": self.authority_touch_rate,
            "philosophy_touch_rate": self.philosophy_touch_rate,
            "metaphor_touch_rate": self.metaphor_touch_rate,
            "safe_candidate_rate": self.safe_candidate_rate,
            "risk_flag_distribution": dict(self.risk_flag_distribution),
            "per_category_trigger": {
                k: dict(v) for k, v in self.per_category_trigger.items()
            },
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_probe_metrics(run: CausalProbeRun) -> ProbeMetrics:
    candidates = run.candidates
    total = len(candidates)

    multistep = [c for c in candidates
                 if c.benchmark_source is BenchmarkSource.MULTISTEP_30]
    main = [c for c in candidates
            if c.benchmark_source is BenchmarkSource.MAIN_50]

    triggered_total = sum(1 for c in candidates if c.candidate_triggered)
    triggered_multi = sum(1 for c in multistep if c.candidate_triggered)
    triggered_main = sum(1 for c in main if c.candidate_triggered)

    triggered_known_fp = sum(
        1 for c in main
        if c.candidate_triggered
        and c.case_id in KNOWN_FALSE_POSITIVE_CASE_IDS
    )

    multistep_rate = _ratio(triggered_multi, len(multistep))
    main_rate = _ratio(triggered_main, len(main))
    known_fp_rate = _ratio(
        triggered_known_fp, len(KNOWN_FALSE_POSITIVE_CASE_IDS),
    )

    flag_counter: Counter[RiskFlag] = Counter()
    for c in candidates:
        for f in c.risk_flags:
            flag_counter[f] += 1
    flag_dist = {f.value: flag_counter.get(f, 0) for f in RiskFlag}

    def _rate(flag: RiskFlag) -> float:
        # rate within the main benchmark — only main-set categories
        # carry these flags by construction.
        n = sum(1 for c in main if flag in c.risk_flags)
        return _ratio(n, len(main))

    authority_rate = _rate(RiskFlag.WOULD_TOUCH_AUTHORITY_CASE)
    philosophy_rate = _rate(RiskFlag.WOULD_TOUCH_PHILOSOPHY_CASE)
    metaphor_rate = _rate(RiskFlag.WOULD_TOUCH_METAPHOR_CASE)

    # "Safe" candidates: triggered AND no risk flag beyond the
    # explicit NO_RISK_FLAG or WOULD_TOUCH_VALID_MULTISTEP_CASE
    # (which is the *desirable* trigger).
    risky_flags = {
        RiskFlag.WOULD_REOPEN_KNOWN_FALSE_POSITIVE,
        RiskFlag.WOULD_TOUCH_AUTHORITY_CASE,
        RiskFlag.WOULD_TOUCH_PHILOSOPHY_CASE,
        RiskFlag.WOULD_TOUCH_METAPHOR_CASE,
        RiskFlag.WOULD_TOUCH_EVERYDAY_CAUSAL_CASE,
        RiskFlag.WOULD_TOUCH_CYCLE_CASE,
        RiskFlag.WOULD_TOUCH_CONTRADICTION_CASE,
    }
    safe = sum(
        1 for c in candidates
        if c.candidate_triggered
        and not (set(c.risk_flags) & risky_flags)
    )
    safe_rate = _ratio(safe, max(1, triggered_total))

    per_category: dict[str, Counter[str]] = {}
    for c in candidates:
        # Tag by a stable composite key
        bucket_key = (
            c.benchmark_source.value + ":"
            + _category_letter(c)
        )
        per_category.setdefault(bucket_key, Counter())[
            "triggered" if c.candidate_triggered else "skipped"
        ] += 1
    per_cat = {k: dict(v) for k, v in per_category.items()}

    return ProbeMetrics(
        total=total,
        triggered_total=triggered_total,
        triggered_multistep=triggered_multi,
        triggered_main=triggered_main,
        triggered_known_false_positives=triggered_known_fp,
        multistep_trigger_rate=multistep_rate,
        main_trigger_rate=main_rate,
        known_false_positive_reopen_rate=known_fp_rate,
        authority_touch_rate=authority_rate,
        philosophy_touch_rate=philosophy_rate,
        metaphor_touch_rate=metaphor_rate,
        safe_candidate_rate=safe_rate,
        risk_flag_distribution=flag_dist,
        per_category_trigger=per_cat,
    )


def _category_letter(c: Any) -> str:
    """Extract the leading-letter category bucket from a case id."""
    cid = c.case_id
    if cid.startswith("R"):
        # R1_01 .. R5_06 -> use first two characters
        return cid[:2]
    # Main cases: A1 .. E10 -> use the first character.
    return cid[:1]


__all__ = ["ProbeMetrics", "compute_probe_metrics"]
