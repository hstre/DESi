"""BridgeEntryAuditRunner — Aufgabe 3.

Runs the 30 v2.3 multi-step cases through proxy-wrapped versions
of the **real** ``LogicalAuditor`` and ``BridgeConsilium``. The
proxies capture telemetry; they never mutate semantics. The real
:class:`RecursiveResolver` then sees the wrapped components — the
walk, the verdicts, the resolution are unchanged.

No production module under ``logic/``, ``consilium/``,
``recursive/``, ``tools/``, ``memory/``, ``evolution/`` or
``spl_adapter/`` is modified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..benchmark_multistep.case import MultiStepCase
from ..consilium import BridgeConsilium
from ..logic import LogicalAuditor
from ..recursive import RecursiveResolver, ResolutionState
from .trace import (
    BridgeEntryTrace,
    classify_loss_stage,
    trace_replay_hash,
)


# ---------------------------------------------------------------------------
# Proxy wrappers — read-only telemetry collectors.
# ---------------------------------------------------------------------------


@dataclass
class _Telemetry:
    """Mutable scratch pad populated by the proxies during one case."""

    audit_calls: int = 0
    last_audit_state: str = ""
    last_premise_kinds: tuple[str, ...] = ()
    last_premise_count: int = 0
    last_bridge_kinds: tuple[str, ...] = ()
    last_bridge_count: int = 0
    consilium_calls: int = 0
    consilium_verdicts: list[str] = field(default_factory=list)
    veto_roles: list[str] = field(default_factory=list)


class _TracingAuditor:
    """Wraps :class:`LogicalAuditor` and records every ``audit()`` call.

    Delegation is exact — the inner auditor's :class:`AuditResult`
    is returned unchanged. This wrapper exists solely to populate
    a :class:`_Telemetry` instance.
    """

    def __init__(
        self,
        inner: LogicalAuditor,
        telemetry: _Telemetry,
    ) -> None:
        self._inner = inner
        self._tel = telemetry

    def audit(self, text: str, **kw: Any) -> Any:
        res = self._inner.audit(text, **kw)
        self._tel.audit_calls += 1
        self._tel.last_audit_state = res.state.value
        self._tel.last_premise_count = len(res.propositions.premises)
        self._tel.last_premise_kinds = tuple(
            p.kind.value for p in res.propositions.premises
        )
        self._tel.last_bridge_count = len(res.bridges)
        self._tel.last_bridge_kinds = tuple(
            getattr(b.kind, "value", str(b.kind)) for b in res.bridges
        )
        return res

    # Pass-through for any attribute the resolver may look up.
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _TracingConsilium:
    """Wraps :class:`BridgeConsilium` and records every ``deliberate()``."""

    def __init__(
        self,
        inner: BridgeConsilium,
        telemetry: _Telemetry,
    ) -> None:
        self._inner = inner
        self._tel = telemetry

    def deliberate(self, bridge: Any, **kw: Any) -> Any:
        res = self._inner.deliberate(bridge, **kw)
        self._tel.consilium_calls += 1
        self._tel.consilium_verdicts.append(res.verdict.verdict.value)
        for r in res.verdict.blocking_roles:
            self._tel.veto_roles.append(getattr(r, "value", str(r)))
        return res

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# Run + report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BridgeAuditRun:
    timestamp: datetime
    traces: tuple[BridgeEntryTrace, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "traces": [t.to_dict() for t in self.traces],
        }


class BridgeEntryAuditRunner:
    """Read-only runner over the v2.3 multi-step cases."""

    def __init__(
        self,
        *,
        cases: tuple[MultiStepCase, ...] = ALL_MULTISTEP_CASES,
    ) -> None:
        self._cases = cases

    def run(self) -> BridgeAuditRun:
        traces: list[BridgeEntryTrace] = []
        for case in self._cases:
            traces.append(self._trace_one(case))
        return BridgeAuditRun(
            timestamp=datetime.now(timezone.utc),
            traces=tuple(traces),
        )

    def _trace_one(self, case: MultiStepCase) -> BridgeEntryTrace:
        tel = _Telemetry()
        auditor = _TracingAuditor(LogicalAuditor(), tel)
        consilium = _TracingConsilium(BridgeConsilium(), tel)
        resolver = RecursiveResolver(
            auditor=auditor, consilium=consilium,
        )
        res = resolver.resolve(case.text)

        parser_recognized = tel.last_premise_count > 0
        bridge_created = tel.last_bridge_count > 0
        consilium_called = tel.consilium_calls > 0
        resolver_entered = res.depth_reached > 0 or consilium_called
        loss_stage = classify_loss_stage(
            parser_recognized=parser_recognized,
            premise_count=tel.last_premise_count,
            audit_state=tel.last_audit_state,
            bridge_created=bridge_created,
            consilium_called=consilium_called,
            consilium_verdicts=tuple(tel.consilium_verdicts),
            veto_roles=tuple(tel.veto_roles),
            resolver_entered=resolver_entered,
            depth_reached=res.depth_reached,
            final_state=res.final_state,
            blocking_reason=res.blocking_reason,
            expected_cycle=case.expected_cycle,
            expected_min_depth=case.expected_min_depth,
            expected_final_state=case.expected_final_state,
            expected_blocked=case.expected_blocked,
        )

        payload = {
            "case_id": case.case_id,
            "parser_recognized": parser_recognized,
            "premise_count": tel.last_premise_count,
            "premise_kinds": list(tel.last_premise_kinds),
            "audit_state": tel.last_audit_state,
            "bridge_created": bridge_created,
            "bridge_count": tel.last_bridge_count,
            "bridge_kinds": list(tel.last_bridge_kinds),
            "consilium_called": consilium_called,
            "consilium_verdicts": list(tel.consilium_verdicts),
            "veto_roles": list(tel.veto_roles),
            "resolver_entered": resolver_entered,
            "depth_reached": res.depth_reached,
            "final_state": res.final_state.value,
            "loss_stage": loss_stage.value,
            "blocking_reason": (
                res.blocking_reason.value if res.blocking_reason else None
            ),
        }
        replay = trace_replay_hash(payload)

        return BridgeEntryTrace(
            case_id=case.case_id,
            parser_recognized=parser_recognized,
            premise_count=tel.last_premise_count,
            premise_kinds=tel.last_premise_kinds,
            audit_state=tel.last_audit_state,
            bridge_created=bridge_created,
            bridge_count=tel.last_bridge_count,
            bridge_kinds=tel.last_bridge_kinds,
            consilium_called=consilium_called,
            consilium_verdicts=tuple(tel.consilium_verdicts),
            veto_roles=tuple(tel.veto_roles),
            resolver_entered=resolver_entered,
            depth_reached=res.depth_reached,
            final_state=res.final_state,
            loss_stage=loss_stage,
            replay_hash=replay,
            blocking_reason=res.blocking_reason,
        )


__all__ = [
    "BridgeAuditRun",
    "BridgeEntryAuditRunner",
]
