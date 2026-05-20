"""Aufgabe 3 — residue case extraction.

Selects every chain in the v4.0 corpus that *still* audits as
``LOGICALLY_SUPPORTED`` under ``CAUSAL_CHAIN`` after the v4.7
patch. Expected count is 9, all in MISSING_BRIDGE_RULE per
the v4.6 taxonomy (the only cluster left after v4.3/v4.5/
v4.7 retired everything else).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import all_chains
from ..external_probe.enums import Domain, GroundTruth
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


EXPECTED_RESIDUE_COUNT: int = 9


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
