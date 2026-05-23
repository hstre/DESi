"""Aufgabe 8 — safe-probe transfer audit.

Takes the six v5.0 safe probes (MT-P01, MT-P02, MT-P03,
MT-P04, MT-P07, MT-P08) and applies them — unmodified — to
every chain in the v5.2 evaluation corpus. The v5.0 probe
implementations are reused directly via ``probe_fires``;
this module never edits them.

Two transfer metrics:

* ``safe_probe_hit_rate`` — for each safe-probe class,
  fraction of v5.2 chains classified into that class on
  which the corresponding probe predicate also fires.
  Reported as the mean across the six probes.
* ``safe_probe_false_activation`` — total count of
  ``(probe, VALID chain)`` pairs where the probe fires
  on a chain whose ground truth is VALID. The v5.0
  contract requires this to be zero on the protected
  pool; v5.2 measures whether the same probes remain safe
  on the new evaluation corpus.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..methodology_transfer.probe_generator import (
    probe_fires,
)
from .classifier import ClassificationResult
from .corpus import GeneralizationChain


SAFE_PROBE_CLASSES: tuple[str, ...] = (
    "MT_MODAL_ASYMMETRY",
    "MT_NEGATION_ASYMMETRY",
    "MT_UNIVERSAL_LEAP",
    "MT_OVERLAP_LOOP",
    "MT_AUDIT_OVER_SUPPORT",
    "MT_AUDIT_OVER_BLOCK",
)


@dataclass(frozen=True)
class ProbeTransferOutcome:
    cluster_name: str
    classified_count: int      # chains classified into this class
    probe_hit_count: int       # probe fired on classified chains
    hit_rate: float
    false_activations: int     # probe fired on a VALID chain

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_name": self.cluster_name,
            "classified_count": self.classified_count,
            "probe_hit_count": self.probe_hit_count,
            "hit_rate": self.hit_rate,
            "false_activations": self.false_activations,
        }


def audit_probe_transfer(
    chains: tuple[GeneralizationChain, ...],
    results: tuple[ClassificationResult, ...],
) -> tuple[ProbeTransferOutcome, ...]:
    text_by_id = {c.chain_id: c.text for c in chains}
    gt_by_id = {c.chain_id: c.ground_truth for c in chains}
    out: list[ProbeTransferOutcome] = []
    for cluster in SAFE_PROBE_CLASSES:
        classified = [
            r for r in results if r.assigned_class == cluster
        ]
        hits = sum(
            1 for r in classified
            if probe_fires(cluster, text_by_id[r.chain_id])
        )
        hit_rate = (
            round(hits / len(classified), 6)
            if classified else 0.0
        )
        false_act = sum(
            1 for c in chains
            if gt_by_id[c.chain_id] == "VALID"
            and probe_fires(cluster, c.text)
        )
        out.append(ProbeTransferOutcome(
            cluster_name=cluster,
            classified_count=len(classified),
            probe_hit_count=hits,
            hit_rate=hit_rate,
            false_activations=false_act,
        ))
    return tuple(out)


def summarise_probe_transfer(
    outcomes: tuple[ProbeTransferOutcome, ...],
) -> tuple[float, int]:
    """Returns ``(safe_probe_hit_rate,
    total_false_activations)``.

    Hit rate is the chain-level rate: total probe hits
    divided by total chains classified into a safe-probe
    class. A probe whose class received no chains
    contributes nothing to either numerator or denominator,
    which is the correct accounting — that probe could not
    demonstrate transfer on this corpus."""
    total_hits = sum(o.probe_hit_count for o in outcomes)
    total_classified = sum(
        o.classified_count for o in outcomes
    )
    mean_hit = (
        round(total_hits / total_classified, 6)
        if total_classified else 0.0
    )
    total_false = sum(o.false_activations for o in outcomes)
    return mean_hit, total_false


__all__ = [
    "ProbeTransferOutcome", "SAFE_PROBE_CLASSES",
    "audit_probe_transfer", "summarise_probe_transfer",
]
