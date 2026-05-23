"""RuleCoverageRunner — Aufgaben 3, 4.

Runs the 30 v2.3 multi-step cases through a read-only proxy around
the real :class:`LogicalAuditor` and uses the existing
:func:`validate_inference` public entry point of v1.2's
``desi.logic`` to observe **which** of the five known rules each
case attempts and which one (if any) matches.

No production module under ``logic/``, ``consilium/``,
``recursive/``, ``tools/``, ``memory/``, ``evolution/`` or
``spl_adapter/`` is modified.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..benchmark_multistep.case import MultiStepCase
from ..logic import LogicalAuditor
from ..logic.inference import InferenceRule, validate_inference
from ..recursive import BlockingReason, RecursiveResolver, ResolutionState
from .categories import AttemptedRule
from .trace import (
    RuleCoverageTrace,
    classify_missing_rule,
    trace_replay_hash,
)


# ---------------------------------------------------------------------------
# Proxy auditor
# ---------------------------------------------------------------------------


@dataclass
class _AuditTelemetry:
    audit_state: str = ""
    premise_count: int = 0
    premise_kinds: tuple[str, ...] = ()
    conclusion_kind: str = ""
    bridge_count: int = 0
    bridge_kinds: tuple[str, ...] = ()
    matched_rule: str | None = None
    attempted_rules: tuple[str, ...] = ()
    no_rule_match: bool = True


class _TracingAuditor:
    """Read-only proxy: forwards every call, records the last audit."""

    def __init__(
        self,
        inner: LogicalAuditor,
        tel: _AuditTelemetry,
    ) -> None:
        self._inner = inner
        self._tel = tel

    def audit(self, text: str, **kw: Any) -> Any:
        res = self._inner.audit(text, **kw)
        props = res.propositions
        self._tel.premise_count = len(props.premises)
        self._tel.premise_kinds = tuple(
            p.kind.value for p in props.premises
        )
        self._tel.conclusion_kind = (
            props.conclusion.kind.value if props.conclusion else ""
        )
        self._tel.audit_state = res.state.value
        self._tel.bridge_count = len(res.bridges)
        self._tel.bridge_kinds = tuple(
            getattr(b.kind, "value", str(b.kind)) for b in res.bridges
        )
        self._tel.matched_rule = (
            res.rule.value if res.rule is not None else None
        )

        # Probe every rule individually via the v1.2 public entry
        # ``validate_inference``. This is *observation*, not
        # alteration — the auditor's own result is unchanged.
        attempted: list[str] = []
        any_match = False
        if props.conclusion is not None:
            for rule in InferenceRule:
                attempted.append(rule.value)
                match = validate_inference(
                    rule, props.premises, props.conclusion,
                )
                if match is not None:
                    any_match = True
        self._tel.attempted_rules = tuple(attempted)
        self._tel.no_rule_match = not any_match
        return res

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# Run + report-builder
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleCoverageRun:
    timestamp: datetime
    traces: tuple[RuleCoverageTrace, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "traces": [t.to_dict() for t in self.traces],
        }


class RuleCoverageRunner:
    """Read-only runner over the v2.3 multi-step cases."""

    def __init__(
        self,
        *,
        cases: tuple[MultiStepCase, ...] = ALL_MULTISTEP_CASES,
    ) -> None:
        self._cases = cases

    def run(self) -> RuleCoverageRun:
        traces = [self._trace_one(c) for c in self._cases]
        return RuleCoverageRun(
            timestamp=datetime.now(timezone.utc),
            traces=tuple(traces),
        )

    def _trace_one(self, case: MultiStepCase) -> RuleCoverageTrace:
        tel = _AuditTelemetry()
        auditor = _TracingAuditor(LogicalAuditor(), tel)
        resolver = RecursiveResolver(auditor=auditor)
        res = resolver.resolve(case.text)

        parser_recognized = tel.premise_count > 0
        bridge_created = tel.bridge_count > 0
        bridge_kind = tel.bridge_kinds[0] if tel.bridge_kinds else None
        rule_attempts = len(tel.attempted_rules)
        missing_class = classify_missing_rule(
            matched_rule=tel.matched_rule,
            premise_count=tel.premise_count,
            premise_kinds=tel.premise_kinds,
            text=case.text,
            expected_cycle=case.expected_cycle,
        )

        payload = {
            "case_id": case.case_id,
            "category": case.category.value,
            "premise_count": tel.premise_count,
            "premise_kinds": list(tel.premise_kinds),
            "conclusion_kind": tel.conclusion_kind,
            "parser_recognized": parser_recognized,
            "audit_state": tel.audit_state,
            "matched_rule": tel.matched_rule,
            "rule_attempts": rule_attempts,
            "attempted_rules": list(tel.attempted_rules),
            "no_rule_match": tel.no_rule_match,
            "bridge_created": bridge_created,
            "bridge_kind": bridge_kind,
            "final_state": res.final_state.value,
            "blocking_reason": (
                res.blocking_reason.value if res.blocking_reason else None
            ),
            "missing_rule_class": missing_class.value,
        }
        replay = trace_replay_hash(payload)

        return RuleCoverageTrace(
            case_id=case.case_id,
            category=case.category.value,
            premise_count=tel.premise_count,
            premise_kinds=tel.premise_kinds,
            conclusion_kind=tel.conclusion_kind,
            parser_recognized=parser_recognized,
            audit_state=tel.audit_state,
            matched_rule=tel.matched_rule,
            rule_attempts=rule_attempts,
            attempted_rules=tel.attempted_rules,
            no_rule_match=tel.no_rule_match,
            bridge_created=bridge_created,
            bridge_kind=bridge_kind,
            final_state=res.final_state,
            blocking_reason=res.blocking_reason,
            missing_rule_class=missing_class,
            replay_hash=replay,
        )


__all__ = ["RuleCoverageRun", "RuleCoverageRunner"]
