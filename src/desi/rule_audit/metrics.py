"""Rule-coverage metrics — Aufgabe 6."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from ..recursive import BlockingReason
from .categories import AttemptedRule, MissingRuleClass
from .runner import RuleCoverageRun


@dataclass(frozen=True)
class RuleCoverageMetrics:
    total: int
    rule_hit_rate: float
    no_rule_match_rate: float
    parser_vs_rule_misclassification_rate: float
    per_rule_hit_counts: dict[str, int]
    missing_rule_distribution: dict[str, int]
    per_category_rule_coverage: dict[str, dict[str, int]]
    multi_hop_case_coverage: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "rule_hit_rate": self.rule_hit_rate,
            "no_rule_match_rate": self.no_rule_match_rate,
            "parser_vs_rule_misclassification_rate":
                self.parser_vs_rule_misclassification_rate,
            "per_rule_hit_counts": dict(self.per_rule_hit_counts),
            "missing_rule_distribution": dict(self.missing_rule_distribution),
            "per_category_rule_coverage": {
                k: dict(v)
                for k, v in self.per_category_rule_coverage.items()
            },
            "multi_hop_case_coverage": self.multi_hop_case_coverage,
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_rule_coverage_metrics(
    run: RuleCoverageRun,
) -> RuleCoverageMetrics:
    traces = run.traces
    total = len(traces)

    # rule_hit_rate: cases where a rule matched at the audit level
    hits = sum(1 for t in traces if t.matched_rule is not None)
    rule_hit_rate = _ratio(hits, total)

    # no_rule_match_rate: cases where none of the five rules fired
    no_match = sum(1 for t in traces if t.no_rule_match)
    no_match_rate = _ratio(no_match, total)

    # parser_vs_rule misclassification: cases blocked with
    # PARSER_UNSUPPORTED_FORM but premises WERE extracted AND no
    # rule matched. These are the "parser is blamed when rules
    # are missing" cases.
    misclassified = sum(
        1 for t in traces
        if t.blocking_reason is BlockingReason.PARSER_UNSUPPORTED_FORM
        and t.parser_recognized
        and t.no_rule_match
    )
    misclass_rate = _ratio(misclassified, total)

    # per-rule hit counts (closed set of 5)
    per_rule: dict[str, int] = {r.value: 0 for r in AttemptedRule}
    for t in traces:
        if t.matched_rule is not None:
            per_rule[t.matched_rule] = per_rule.get(t.matched_rule, 0) + 1

    # missing_rule_distribution over the closed 7-value enum
    miss_dist: dict[str, int] = {m.value: 0 for m in MissingRuleClass}
    for t in traces:
        miss_dist[t.missing_rule_class.value] += 1

    # per-category coverage: category → matched-rule histogram
    by_category: dict[str, Counter[str]] = {}
    for t in traces:
        by_category.setdefault(t.category, Counter())[
            t.matched_rule or "no_rule_match"
        ] += 1
    per_category = {
        cat: dict(counter) for cat, counter in by_category.items()
    }

    # multi-hop case coverage: of the R2+R3 cases (those that
    # genuinely require multi-hop), what fraction had a rule match?
    multi_hop = [
        t for t in traces if t.category in (
            "R2_three_step_bridge", "R3_four_step_closure",
        )
    ]
    multi_hop_hits = sum(1 for t in multi_hop if t.matched_rule is not None)
    multi_hop_coverage = _ratio(multi_hop_hits, len(multi_hop))

    return RuleCoverageMetrics(
        total=total,
        rule_hit_rate=rule_hit_rate,
        no_rule_match_rate=no_match_rate,
        parser_vs_rule_misclassification_rate=misclass_rate,
        per_rule_hit_counts=per_rule,
        missing_rule_distribution=miss_dist,
        per_category_rule_coverage=per_category,
        multi_hop_case_coverage=multi_hop_coverage,
    )


def dominant_missing_rule_class(
    metrics: RuleCoverageMetrics,
) -> MissingRuleClass:
    """The most frequent non-NONE missing-rule class.

    Deterministic tie-break: enum declaration order.
    """
    counts = metrics.missing_rule_distribution
    table = [(m, counts.get(m.value, 0)) for m in MissingRuleClass
             if m is not MissingRuleClass.NONE]
    best = max(table, key=lambda kv: kv[1])
    if best[1] == 0:
        return MissingRuleClass.NONE
    return best[0]


__all__ = [
    "RuleCoverageMetrics",
    "compute_rule_coverage_metrics",
    "dominant_missing_rule_class",
]
