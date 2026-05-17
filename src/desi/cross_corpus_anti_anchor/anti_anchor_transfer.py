"""v3.55 — anti-anchor transfer aggregator.

Per-corpus suppression records are aggregated into a
transfer rate: a corpus is "transferred" iff the
v3.51 success criteria (suppression >= MIN_SUPPRESSION
AND plateau_recall >= MIN_TARGET_RECALL) both hold.
"""
from __future__ import annotations

from .suppression import (
    CorpusSuppressionRecord,
    all_corpus_suppression_records,
)


MIN_TARGET_RECALL: float = 0.90
MIN_SUPPRESSION:   float = 0.80


def transfers_at(
    rec: CorpusSuppressionRecord,
) -> bool:
    return (
        rec.plateau_recall >= MIN_TARGET_RECALL
        and rec.suppression_fraction >= MIN_SUPPRESSION
    )


def transfer_rate(
    records: tuple[CorpusSuppressionRecord, ...],
) -> float:
    eligible = [
        r for r in records
        if r.baseline_leakage > 0
        and r.plateau_count > 0
    ]
    if not eligible:
        return 0.0
    return round(
        sum(1 for r in eligible if transfers_at(r))
        / len(eligible),
        6,
    )


def aggregate() -> tuple[
    tuple[CorpusSuppressionRecord, ...], float,
]:
    records = all_corpus_suppression_records()
    return records, transfer_rate(records)


__all__ = [
    "MIN_SUPPRESSION", "MIN_TARGET_RECALL",
    "aggregate", "transfer_rate", "transfers_at",
]
