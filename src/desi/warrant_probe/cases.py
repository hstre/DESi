"""Aufgabe 3 — residual case extraction.

Selects every chain in the v4.0 corpus that *still* audits
as ``LOGICALLY_SUPPORTED`` under ``CAUSAL_CHAIN`` after the
v4.5 patch. Expected count is 19 (v4.3 retired 119; v4.5
retired 5 more; what survives is the 19 the directive
addresses).

No new chains; this is a strict subset of the v4.0 external
corpus.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import all_chains
from ..external_probe.enums import Domain, GroundTruth
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


EXPECTED_RESIDUE_COUNT: int = 19


@dataclass(frozen=True)
class ResidueCase:
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


def collect_residue_cases() -> tuple[ResidueCase, ...]:
    """Deterministic, in corpus order. Uses the v4.5-patched
    auditor."""
    auditor = LogicalAuditor()
    out: list[ResidueCase] = []
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
            out.append(ResidueCase(
                chain_id=c.chain_id, domain=c.domain.value,
                text=c.text, ground_truth=c.ground_truth.value,
            ))
    return tuple(out)


__all__ = [
    "EXPECTED_RESIDUE_COUNT", "ResidueCase",
    "collect_residue_cases",
]
