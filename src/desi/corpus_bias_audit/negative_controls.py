"""Aufgabe 9 — 100+ adversarial rewrite NCs.

Five closed NC kinds (``NCKind``):

* PROBE_ALIGNED_FAKE_INVALID  — RAW had no safe probe
  firing; FINAL adds strict-vocabulary trigger. Expected
  rewrite_kind == ``probe_alignment``.
* PROBE_AVOIDING_FAKE_VALID   — RAW fires a safe probe;
  FINAL rewrites it away. Expected
  rewrite_kind == ``probe_avoidance``.
* SEMANTIC_PARAPHRASE_TRAP    — RAW and FINAL differ
  substantially in wording but neither fires any safe
  probe (label preserved, no probe delta).
  Expected rewrite_kind == ``semantic_paraphrase``
  (or ``none`` if the texts happen to share enough tokens
  that the audit calls them identical).
* LABEL_PRESERVING_SHIFT      — Minimal lexical edit
  preserving label. No probe delta.
* CROSS_DOMAIN_REWRITE        — Conclusion's domain
  vocabulary swapped (e.g. legal → medical) with no
  change to probe-trigger surface signals.

Accuracy = fraction of NCs whose ``audit_pair`` output
matches the expected rewrite_kind.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..taxonomy_generalization.corpus import (
    GeneralizationChain,
)
from .diff import audit_pair
from .enums import NCKind, RewriteKind
from .raw_corpus import ChainPair


@dataclass(frozen=True)
class RewriteNC:
    nc_id: str
    kind: str
    expected_rewrite_kind: str
    raw_text: str
    final_text: str
    domain: str
    ground_truth: str


def _make(
    prefix: str, items: tuple[tuple[str, str], ...],
    kind: NCKind, expected: RewriteKind, domain: str,
    ground_truth: str,
) -> tuple[RewriteNC, ...]:
    return tuple(
        RewriteNC(
            nc_id=f"{prefix}{i:03d}", kind=kind.value,
            expected_rewrite_kind=expected.value,
            raw_text=raw, final_text=final,
            domain=domain, ground_truth=ground_truth,
        )
        for i, (raw, final) in enumerate(items, start=1)
    )


# ---------------------------------------------------------------------------
# PROBE_ALIGNED_FAKE_INVALID
# RAW (no probe), FINAL (strict modal "will" or
# multi-word "every X") -> alignment
# ---------------------------------------------------------------------------

_ALIGNED = tuple(
    (
        f"Premise alpha {i}. Premise beta {i}. Therefore "
        f"the team concluded the matter at sample {i}.",
        f"Premise alpha {i}. Premise beta {i}. Therefore "
        f"the team will conclude the matter for every "
        f"comparable sample like {i}.",
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# PROBE_AVOIDING_FAKE_VALID
# RAW (fires OVERLAP_LOOP via heavy concl-premise token
# repetition), FINAL (fresh conclusion vocabulary)
# ---------------------------------------------------------------------------

_AVOIDING = tuple(
    (
        f"Productivity in zone {i} rose during the {i} "
        f"period. Audit findings in zone {i} cleared "
        f"each {i} review. Therefore productivity in "
        f"zone {i} rose across the zone {i} review.",
        f"Productivity in zone {i} rose during the {i} "
        f"period. Audit findings in zone {i} cleared "
        f"each {i} review. Therefore output metrics held "
        f"within tolerance through the subsequent "
        f"observation window.",
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# SEMANTIC_PARAPHRASE_TRAP
# RAW and FINAL differ in vocabulary but neither fires
# any safe probe (no strict modal, no strict negation,
# no multi-word universal, no overlap loop).
# ---------------------------------------------------------------------------

_PARAPHRASE = tuple(
    (
        f"The crew assembled tooling early. The "
        f"technician inspected gauges {i}. Therefore "
        f"installation proceeded steadily through the "
        f"morning shift.",
        f"The crew prepared equipment ahead of time. "
        f"The technician examined readings {i}. "
        f"Therefore deployment advanced steadily over "
        f"the morning rotation.",
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# LABEL_PRESERVING_SHIFT
# Same RAW and FINAL — no rewrite. Expected: rewrite_kind
# == "none".
# ---------------------------------------------------------------------------

_LABEL_PRESERVING = tuple(
    (
        f"The lab logged steady readings on day {i}. "
        f"The technician compiled the report. Therefore "
        f"the documented values aligned with the prior "
        f"baseline on day {i}.",
        f"The lab logged steady readings on day {i}. "
        f"The technician compiled the report. Therefore "
        f"the documented values aligned with the prior "
        f"baseline on day {i}.",
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# CROSS_DOMAIN_REWRITE
# RAW (engineering vocabulary) vs FINAL (medical
# vocabulary), no probe delta, conclusion novelty
# similar.
# ---------------------------------------------------------------------------

_CROSS_DOMAIN = tuple(
    (
        f"The platform team reviewed the rollout {i}. "
        f"Operators logged the change. Therefore the "
        f"system advanced steadily through the validation "
        f"interval {i}.",
        f"The clinical team reviewed the protocol {i}. "
        f"Nurses logged the administration. Therefore "
        f"the regimen advanced steadily through the "
        f"observation interval {i}.",
    )
    for i in range(1, 21)
)


def all_rewrite_ncs() -> tuple[RewriteNC, ...]:
    return (
        _make(
            "NC-PA-", _ALIGNED,
            NCKind.PROBE_ALIGNED_FAKE_INVALID,
            RewriteKind.PROBE_ALIGNMENT,
            "synthetic", "INVALID",
        )
        + _make(
            "NC-PV-", _AVOIDING,
            NCKind.PROBE_AVOIDING_FAKE_VALID,
            RewriteKind.PROBE_AVOIDANCE,
            "synthetic", "VALID",
        )
        + _make(
            "NC-SP-", _PARAPHRASE,
            NCKind.SEMANTIC_PARAPHRASE_TRAP,
            RewriteKind.SEMANTIC_PARAPHRASE,
            "synthetic", "VALID",
        )
        + _make(
            "NC-LP-", _LABEL_PRESERVING,
            NCKind.LABEL_PRESERVING_SHIFT,
            RewriteKind.NONE,
            "synthetic", "VALID",
        )
        + _make(
            "NC-CD-", _CROSS_DOMAIN,
            NCKind.CROSS_DOMAIN_REWRITE,
            RewriteKind.SEMANTIC_PARAPHRASE,
            "synthetic", "VALID",
        )
    )


def classify_nc(nc: RewriteNC) -> str:
    pair = ChainPair(
        chain_id=nc.nc_id, domain=nc.domain,
        ground_truth=nc.ground_truth,
        raw_text=nc.raw_text, final_text=nc.final_text,
        was_rewritten=nc.raw_text != nc.final_text,
    )
    return audit_pair(pair).rewrite_kind


def classification_accuracy() -> float:
    ncs = all_rewrite_ncs()
    correct = sum(
        1 for nc in ncs
        if classify_nc(nc) == nc.expected_rewrite_kind
    )
    return round(correct / len(ncs), 6)


__all__ = [
    "RewriteNC", "all_rewrite_ncs",
    "classification_accuracy", "classify_nc",
]
