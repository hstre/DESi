"""Aufgabe 7 — probe-only metrics on the RAW corpus.

The six v5.0 safe probes are imported via the v5.2
``audit_probe_transfer`` helper, unchanged. The v5.2
classification is reused to define each probe's eligible
chains (chains classified into the probe's cluster).
Every number declares ``RawEvalChannel.PROBE_ONLY``.

The directive forbids aggregation of taxonomy and probe
metrics, so this module never reports a combined number.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..methodology_transfer.probe_generator import (
    probe_fires,
)
from ..taxonomy_generalization.classifier import (
    ClassificationResult, classify_all,
)
from ..taxonomy_generalization.corpus import (
    GeneralizationChain,
)
from ..taxonomy_generalization.probe_transfer import (
    SAFE_PROBE_CLASSES, ProbeTransferOutcome,
    audit_probe_transfer, summarise_probe_transfer,
)
from ..taxonomy_generalization.report import build_report
from .enums import RawEvalChannel


@dataclass(frozen=True)
class ProbeMetrics:
    channel: str  # always probe_only
    probe_hit_rate: float
    probe_false_activation: int
    probe_domain_variance: float
    probe_alignment_loss: float  # v5.2 FINAL hit_rate - RAW hit_rate
    outcomes: tuple[ProbeTransferOutcome, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "probe_hit_rate": self.probe_hit_rate,
            "probe_false_activation":
                self.probe_false_activation,
            "probe_domain_variance":
                self.probe_domain_variance,
            "probe_alignment_loss":
                self.probe_alignment_loss,
            "outcomes": [
                o.to_dict() for o in self.outcomes
            ],
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _variance(xs: list[float]) -> float:
    if not xs:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def evaluate_probes(
    chains: tuple[GeneralizationChain, ...],
    results: tuple[ClassificationResult, ...] | None = None,
) -> ProbeMetrics:
    if results is None:
        results = classify_all(chains)
    outcomes = audit_probe_transfer(chains, results)
    hit_rate, false_act = summarise_probe_transfer(outcomes)

    # Per-domain probe-hit rate variance.
    per_domain_hits: dict[str, list[float]] = defaultdict(list)
    text_by_id = {c.chain_id: c.text for c in chains}
    domain_by_id = {c.chain_id: c.domain for c in chains}
    for cluster in SAFE_PROBE_CLASSES:
        classified = [
            r for r in results if r.assigned_class == cluster
        ]
        # Group by domain for that cluster.
        by_dom: dict[str, list[int]] = defaultdict(list)
        for r in classified:
            fired = probe_fires(cluster, text_by_id[r.chain_id])
            by_dom[domain_by_id[r.chain_id]].append(
                1 if fired else 0,
            )
        for dom, vals in by_dom.items():
            per_domain_hits[dom].append(
                sum(vals) / len(vals) if vals else 0.0,
            )
    domain_means = [
        sum(v) / len(v) if v else 0.0
        for v in per_domain_hits.values()
    ]
    probe_dom_var = _variance(domain_means)

    final_report = build_report()
    final_hit = final_report.safe_probe_hit_rate
    alignment_loss = final_hit - hit_rate

    return ProbeMetrics(
        channel=RawEvalChannel.PROBE_ONLY.value,
        probe_hit_rate=_round(hit_rate),
        probe_false_activation=int(false_act),
        probe_domain_variance=_round(probe_dom_var),
        probe_alignment_loss=_round(alignment_loss),
        outcomes=outcomes,
    )


__all__ = ["ProbeMetrics", "evaluate_probes"]
