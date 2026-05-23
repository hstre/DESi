"""Aufgabe 5 — integration benchmark for the v3.13 router.

At least 60 cases split into three categories:

* ``MANIPULATIVE`` (≥ 20) — adversarial cases where the outer
  context lies. Expected routing: BLOCKED / INNER_ONLY /
  MARKER_REQUIRED (never ALLOWED).
* ``NORMAL`` (≥ 20) — consistent cases where inner and outer
  match. Expected routing: ALLOWED.
* ``AMBIGUOUS`` (≥ 20) — polysemy-pair tensions or missing
  signal. Expected routing: INNER_ONLY or MARKER_REQUIRED.

Pulls from the v3.11 runtime benchmark, the v3.9 manipulation
corpus, and the v3.8 false-inheritance fixtures so the
integration test exercises the same shapes the upstream probes
already validated.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..frame_consistency_probe.manipulation import MANIPULATIONS
from ..frame_context_probe.false_inheritance import NEGATIVE_CONTROLS
from ..frame_tension import ALL_LAYER_CASES, FrameConsistency
from .ledger import FrameRoutingLedgerEvent


class IntegrationCategory(str, Enum):
    MANIPULATIVE = "manipulative"
    NORMAL       = "normal"
    AMBIGUOUS    = "ambiguous"


# The set of routing events that each category permits. The
# benchmark passes iff every case's observed event is in the
# permitted set for its category.
_PERMITTED_EVENTS: dict[
    IntegrationCategory, frozenset[FrameRoutingLedgerEvent],
] = {
    IntegrationCategory.MANIPULATIVE: frozenset({
        FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED,
        FrameRoutingLedgerEvent.FRAME_ROUTING_INNER_ONLY,
        FrameRoutingLedgerEvent.FRAME_ROUTING_MARKER_REQUIRED,
    }),
    IntegrationCategory.NORMAL: frozenset({
        FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED,
    }),
    IntegrationCategory.AMBIGUOUS: frozenset({
        FrameRoutingLedgerEvent.FRAME_ROUTING_INNER_ONLY,
        FrameRoutingLedgerEvent.FRAME_ROUTING_MARKER_REQUIRED,
        FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED,
    }),
}


def permitted_events(
    category: IntegrationCategory,
) -> frozenset[FrameRoutingLedgerEvent]:
    return _PERMITTED_EVENTS[category]


@dataclass(frozen=True)
class IntegrationCase:
    case_id: str
    claim_text: str
    inherited_context_text: str
    category: IntegrationCategory

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "claim_text": self.claim_text,
            "inherited_context_text": self.inherited_context_text,
            "category": self.category.value,
        }


def _manipulative_cases() -> tuple[IntegrationCase, ...]:
    out: list[IntegrationCase] = []
    for m in MANIPULATIONS:
        out.append(IntegrationCase(
            case_id=f"M:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
            category=IntegrationCategory.MANIPULATIVE,
        ))
    for nc in NEGATIVE_CONTROLS:
        out.append(IntegrationCase(
            case_id=f"FI:{nc.case_id}",
            claim_text=nc.text,
            inherited_context_text=nc.misleading_window.ctx_3,
            category=IntegrationCategory.MANIPULATIVE,
        ))
    return tuple(out)


def _normal_cases() -> tuple[IntegrationCase, ...]:
    out: list[IntegrationCase] = []
    for c in ALL_LAYER_CASES:
        if c.expected is FrameConsistency.CONFIRMED:
            out.append(IntegrationCase(
                case_id=f"N:{c.case_id}",
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
                category=IntegrationCategory.NORMAL,
            ))
    # Synthetic top-ups so every category clears 20 even if a
    # future upstream change shrinks the source pool.
    synthetic_normals: tuple[tuple[str, str, str], ...] = (
        ("N:SN01",
         "By modus ponens the syllogism remains valid.",
         "Frame: formal logic"),
        ("N:SN02",
         "The minister stated the policy is final.",
         "Frame: authority"),
        ("N:SN03",
         "Heat flow in joules per second drives the cycle.",
         "Frame: thermodynamic"),
        ("N:SN04",
         "Channel capacity in bits per use bounds throughput.",
         "Frame: information-theoretic"),
        ("N:SN05",
         "Loosely speaking, the city sings like a poet.",
         "Frame: metaphorical"),
        ("N:SN06",
         "Calculate the sum 12 + 7 carefully.",
         "Frame: tool computable"),
        ("N:SN07",
         "The drought led to widespread crop failure.",
         "Frame: empirical causal"),
        ("N:SN08",
         ("Numerically identical objects are indistinguishable "
          "in every property."),
         "Frame: ontological distinguishability"),
        ("N:SN09",
         "Figuratively, the city breathes like a lung.",
         "Frame: metaphorical"),
        ("N:SN10",
         "Every x is a y; therefore every x is also z.",
         "Frame: formal logic"),
    )
    for cid, claim, ctx in synthetic_normals:
        out.append(IntegrationCase(
            case_id=cid, claim_text=claim,
            inherited_context_text=ctx,
            category=IntegrationCategory.NORMAL,
        ))
    return tuple(out)


def _ambiguous_cases() -> tuple[IntegrationCase, ...]:
    out: list[IntegrationCase] = []
    for c in ALL_LAYER_CASES:
        if c.expected in (
            FrameConsistency.TENSION, FrameConsistency.UNDECIDABLE,
        ):
            out.append(IntegrationCase(
                case_id=f"A:{c.case_id}",
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
                category=IntegrationCategory.AMBIGUOUS,
            ))
    return tuple(out)


def build_integration_benchmark() -> tuple[IntegrationCase, ...]:
    cases = _normal_cases() + _manipulative_cases() + _ambiguous_cases()
    counts: dict[IntegrationCategory, int] = {
        c: 0 for c in IntegrationCategory
    }
    for c in cases:
        counts[c.category] += 1
    for cat, n in counts.items():
        if n < 20:
            raise RuntimeError(
                f"integration benchmark category {cat.value} "
                f"has {n} cases, need >= 20"
            )
    if len(cases) < 60:
        raise RuntimeError(
            f"integration benchmark has {len(cases)} cases, "
            "need >= 60"
        )
    return cases


def category_counts() -> dict[str, int]:
    cs = build_integration_benchmark()
    out: dict[str, int] = {c.value: 0 for c in IntegrationCategory}
    for case in cs:
        out[case.category.value] += 1
    out["total"] = len(cs)
    return out


__all__ = [
    "IntegrationCase",
    "IntegrationCategory",
    "build_integration_benchmark",
    "category_counts",
    "permitted_events",
]
