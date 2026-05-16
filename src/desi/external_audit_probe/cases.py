"""Aufgabe 3 — false-support case extraction.

Pulls the v4.0 corpus (== the v4.1 corpus), runs each chain
through the unmodified ``LogicalAuditor``, and keeps the
INVALID chains for which the audit returns
``LOGICALLY_SUPPORTED`` under ``CAUSAL_CHAIN``. The expected
count is 143 — matching v4.1's deeper-instrumentation finding.

No new chains are created here; the case set is purely a
*selection* of the existing v4.0 corpus.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import ExternalChain, all_chains
from ..external_probe.enums import Domain, GroundTruth
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


@dataclass(frozen=True)
class FalseSupportCase:
    chain_id: str
    domain: str
    text: str
    ground_truth: str

    def to_dict(self) -> dict[str, str]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "text": self.text,
            "ground_truth": self.ground_truth,
        }


def collect_false_support_cases() -> tuple[FalseSupportCase, ...]:
    """Deterministic collection in v4.0 corpus order."""
    auditor = LogicalAuditor()
    cases: list[FalseSupportCase] = []
    for c in all_chains():
        if c.ground_truth is not GroundTruth.INVALID:
            continue
        if c.domain is Domain.NEGATIVE_CONTROL:
            continue
        a = auditor.audit(c.text)
        if (
            a.state is LogicalState.LOGICALLY_SUPPORTED
            and a.rule is InferenceRule.CAUSAL_CHAIN
        ):
            cases.append(FalseSupportCase(
                chain_id=c.chain_id, domain=c.domain.value,
                text=c.text, ground_truth=c.ground_truth.value,
            ))
    return tuple(cases)


__all__ = ["FalseSupportCase", "collect_false_support_cases"]
