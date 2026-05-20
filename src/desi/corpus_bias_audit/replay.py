"""Aufgabe 7 / 8 — counterfactual replay on RAW corpus.

The canonical v5.0 taxonomy and the six safe v5.0 probes
are applied — unchanged — to the RAW corpus, and the
resulting coverage / probe-transfer / false-activation
numbers are compared to the FINAL v5.2 numbers. The
*gain* attributable to rewriting is the difference.

This module imports the v5.2 classifier and probe-audit
infrastructure unmodified. Only the input corpus differs.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..taxonomy_generalization.classifier import (
    classify_all,
)
from ..taxonomy_generalization.probe_transfer import (
    audit_probe_transfer, summarise_probe_transfer,
)
from ..taxonomy_generalization.report import build_report
from .raw_corpus import raw_chains


@dataclass(frozen=True)
class ReplayOutcome:
    corpus_label: str  # "FINAL" or "RAW"
    taxonomy_coverage: float
    unknown_fraction: float
    safe_probe_hit_rate: float
    safe_probe_false_activation: int
    probe_transfer_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_label": self.corpus_label,
            "taxonomy_coverage": self.taxonomy_coverage,
            "unknown_fraction": self.unknown_fraction,
            "safe_probe_hit_rate":
                self.safe_probe_hit_rate,
            "safe_probe_false_activation":
                self.safe_probe_false_activation,
            "probe_transfer_rate":
                self.probe_transfer_rate,
        }


@dataclass(frozen=True)
class RewriteInfluence:
    coverage_gain_from_rewrites: float
    probe_gain_from_rewrites: float
    false_activation_reduction: int

    def to_dict(self) -> dict[str, object]:
        return {
            "coverage_gain_from_rewrites":
                self.coverage_gain_from_rewrites,
            "probe_gain_from_rewrites":
                self.probe_gain_from_rewrites,
            "false_activation_reduction":
                self.false_activation_reduction,
        }


def replay_raw() -> ReplayOutcome:
    chains = raw_chains()
    results = classify_all(chains)
    outcomes = audit_probe_transfer(chains, results)
    hit, false_act = summarise_probe_transfer(outcomes)
    total = len(results)
    unknown = sum(
        1 for r in results if r.assigned_class == "UNKNOWN"
    )
    return ReplayOutcome(
        corpus_label="RAW",
        taxonomy_coverage=round(
            (total - unknown) / total, 6,
        ) if total else 0.0,
        unknown_fraction=round(
            unknown / total, 6,
        ) if total else 0.0,
        safe_probe_hit_rate=hit,
        safe_probe_false_activation=false_act,
        probe_transfer_rate=hit,
    )


def replay_final() -> ReplayOutcome:
    r = build_report()
    return ReplayOutcome(
        corpus_label="FINAL",
        taxonomy_coverage=r.metrics.taxonomy_coverage,
        unknown_fraction=r.metrics.unknown_fraction,
        safe_probe_hit_rate=r.safe_probe_hit_rate,
        safe_probe_false_activation=(
            r.safe_probe_false_activation
        ),
        probe_transfer_rate=r.metrics.probe_transfer_rate,
    )


def compute_rewrite_influence(
    raw: ReplayOutcome, final: ReplayOutcome,
) -> RewriteInfluence:
    return RewriteInfluence(
        coverage_gain_from_rewrites=round(
            final.taxonomy_coverage - raw.taxonomy_coverage,
            6,
        ),
        probe_gain_from_rewrites=round(
            final.probe_transfer_rate
            - raw.probe_transfer_rate,
            6,
        ),
        false_activation_reduction=(
            raw.safe_probe_false_activation
            - final.safe_probe_false_activation
        ),
    )


__all__ = [
    "ReplayOutcome", "RewriteInfluence",
    "compute_rewrite_influence", "replay_final",
    "replay_raw",
]
