"""RuleCoverageTrace + MissingRuleClass classifier — Aufgabe 2 + 5.

The trace is populated by :mod:`rule_audit.runner`; the classifier
projects each trace onto exactly one :class:`MissingRuleClass`
value using deterministic, data-only inspection of:

* number and kinds of premises extracted by the auditor,
* number of "Therefore" markers in the original text,
* presence of temporal connectives ("then", "after", "before",
  "later"),
* the case's hand-labelled ``expected_cycle``.

Nothing here adds a new inference capability. The classifier
labels what's already observable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..recursive import BlockingReason, ResolutionState
from .categories import MissingRuleClass


@dataclass(frozen=True)
class RuleCoverageTrace:
    """Per-case observation of inference-rule coverage."""

    case_id: str
    category: str
    premise_count: int
    premise_kinds: tuple[str, ...]
    conclusion_kind: str
    parser_recognized: bool
    audit_state: str
    matched_rule: str | None
    rule_attempts: int
    attempted_rules: tuple[str, ...]
    no_rule_match: bool
    bridge_created: bool
    bridge_kind: str | None
    final_state: ResolutionState
    blocking_reason: BlockingReason | None
    missing_rule_class: MissingRuleClass
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "premise_count": self.premise_count,
            "premise_kinds": list(self.premise_kinds),
            "conclusion_kind": self.conclusion_kind,
            "parser_recognized": self.parser_recognized,
            "audit_state": self.audit_state,
            "matched_rule": self.matched_rule,
            "rule_attempts": self.rule_attempts,
            "attempted_rules": list(self.attempted_rules),
            "no_rule_match": self.no_rule_match,
            "bridge_created": self.bridge_created,
            "bridge_kind": self.bridge_kind,
            "final_state": self.final_state.value,
            "blocking_reason": (
                self.blocking_reason.value if self.blocking_reason else None
            ),
            "missing_rule_class": self.missing_rule_class.value,
            "replay_hash": self.replay_hash,
        }


# ---------------------------------------------------------------------------
# Classification — deterministic projection from observed data.
# ---------------------------------------------------------------------------


_TEMPORAL_MARKERS = ("then", "after", "before", "later", "subsequently")


def _count_markers(text: str, marker: str) -> int:
    """Lower-case substring count — no regex per directive."""
    lo = text.lower()
    n = 0
    start = 0
    while True:
        i = lo.find(marker, start)
        if i < 0:
            break
        n += 1
        start = i + len(marker)
    return n


def classify_missing_rule(
    *,
    matched_rule: str | None,
    premise_count: int,
    premise_kinds: tuple[str, ...],
    text: str,
    expected_cycle: bool,
) -> MissingRuleClass:
    """Project a trace into exactly one ``MissingRuleClass`` value.

    Order of checks is documented and stable. The classifier is a
    *labeller*, not a new heuristic — it adds no reasoning, it only
    names what the data already shows.
    """
    if matched_rule is not None:
        return MissingRuleClass.NONE

    # Cycle structures are tagged from the case label; we trust the
    # author-supplied ``expected_cycle`` rather than re-parsing the
    # text for cycle hints.
    if expected_cycle:
        return MissingRuleClass.CYCLE_STRUCTURAL

    therefore_count = _count_markers(text, "therefore")
    conditional_count = sum(
        1 for k in premise_kinds
        if k in ("conditional", "implication")
    )
    has_temporal = any(_count_markers(text, m) > 0 for m in _TEMPORAL_MARKERS)

    # Chained-conditional / multi-hop wins over plain causal when
    # the premise kinds carry explicit conditional structure.
    if conditional_count >= 2:
        # Multi-hop implication is the v1.2 ``TRANSITIVITY`` form
        # extended past two hops; chained-conditional is the
        # general "if A then B; if B then C; if C then D" shape.
        return (
            MissingRuleClass.MULTI_HOP_IMPLICATION
            if therefore_count >= 1 and premise_count >= 3
            else MissingRuleClass.CHAINED_CONDITIONAL
        )

    # Causal chains: either explicit ("Therefore X. Therefore Y.")
    # or implicit (sequential atomic premises with one conclusion).
    # Either pattern signals the same missing rule family.
    if therefore_count >= 2:
        return MissingRuleClass.CAUSAL_CHAIN
    if premise_count >= 3 and therefore_count >= 1:
        return MissingRuleClass.CAUSAL_CHAIN

    # Temporal chains: temporal connectives + sequential premises.
    if has_temporal and premise_count >= 2:
        return MissingRuleClass.CHAINED_TEMPORAL

    return MissingRuleClass.UNKNOWN


def trace_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items() if k != "replay_hash"}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "RuleCoverageTrace",
    "classify_missing_rule",
    "trace_replay_hash",
]
