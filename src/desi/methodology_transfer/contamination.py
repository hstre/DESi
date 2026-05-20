"""Aufgabe 8 — contamination audit against the protected
pool.

Each candidate probe is tested against every VALID-labeled
chain in the protected pool (v1.5, v2.3, v2.7, v3.14,
v4.0-v4.12). A probe is *safe* iff it fires on zero
protected chains.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..external_probe.corpus import all_chains as v40_chains
from ..external_probe.enums import GroundTruth
from ..heldout_causal import ALL_HELDOUT_CASES
from ..tools.benchmark import ALL_TOOL_CASES
from .probe_generator import probe_fires


def _protected_pool() -> tuple[str, ...]:
    """Mirror the v4.3 / v4.5 / v4.7 / v4.9 protected-pool
    definition: only chains that currently audit as
    ``LOGICALLY_SUPPORTED`` AND carry VALID ground truth.
    A probe firing on any of these is a false-negative
    regression candidate."""
    from ..logic.audit import LogicalAuditor, LogicalState
    auditor = LogicalAuditor()
    pool: list[str] = []
    sources: list[tuple[str, object]] = []
    for c in MAIN_CASES:
        sources.append(("main", c.text))
    for c in ALL_MULTISTEP_CASES:
        sources.append(("mult", c.text))
    for c in ALL_HELDOUT_CASES:
        sources.append(("held", c.text))
    for c in ALL_ADVERSARIAL_CASES:
        sources.append(("adv", c.text))
    for c in ALL_TOOL_CASES:
        sources.append(("tool", c.text))
    for c in v40_chains():
        if c.ground_truth is GroundTruth.VALID:
            sources.append(("v40-valid", c.text))
    for _src, text in sources:
        if auditor.audit(text).state is (
            LogicalState.LOGICALLY_SUPPORTED
        ):
            pool.append(text)
    return tuple(pool)


@dataclass(frozen=True)
class ProbeAuditOutcome:
    probe_id: str
    cluster_name: str
    rescued_cases: int
    rescue_rate: float
    contamination: int
    safe: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "cluster_name": self.cluster_name,
            "rescued_cases": self.rescued_cases,
            "rescue_rate": self.rescue_rate,
            "contamination": self.contamination,
            "safe": self.safe,
        }


def audit_probes(
    probes_by_cluster: dict[str, str],
    cluster_member_texts: dict[str, tuple[str, ...]],
) -> tuple[ProbeAuditOutcome, ...]:
    """Audit one probe per cluster.

    ``probes_by_cluster``: cluster_name -> probe_id.
    ``cluster_member_texts``: cluster_name -> tuple of
    member chain texts (rescuability is measured here).
    """
    protected = _protected_pool()
    out: list[ProbeAuditOutcome] = []
    for cluster_name, probe_id in probes_by_cluster.items():
        members = cluster_member_texts.get(cluster_name, ())
        rescued = sum(
            1 for t in members
            if probe_fires(cluster_name, t)
        )
        rate = (
            round(rescued / len(members), 6)
            if members else 0.0
        )
        contam = sum(
            1 for t in protected
            if probe_fires(cluster_name, t)
        )
        out.append(ProbeAuditOutcome(
            probe_id=probe_id,
            cluster_name=cluster_name,
            rescued_cases=rescued,
            rescue_rate=rate,
            contamination=contam,
            safe=(contam == 0),
        ))
    return tuple(out)


__all__ = [
    "ProbeAuditOutcome", "_protected_pool", "audit_probes",
]
