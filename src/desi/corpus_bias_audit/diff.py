"""Aufgabe 5 — per-chain rewrite audit.

For every chain pair (RAW, FINAL) we compute:

* ``token_edit_distance``  — number of token-level
  differences (insertions + deletions).
* ``probe_alignment_delta`` — count of *new* safe-probe
  activations introduced by the rewrite (typically on
  INVALID chains: the FINAL version uses strict probe
  vocabulary, so the probe now fires).
* ``probe_avoidance_delta`` — count of safe-probe
  activations *removed* by the rewrite (typically on
  VALID chains: the RAW version triggered a probe that
  the FINAL version avoids).
* ``semantic_similarity``  — Jaccard similarity over
  content tokens.
* ``label_preservation``   — whether the rewrite kept the
  same ground-truth label.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..methodology_transfer.feature_extraction import (
    _content_tokens, _all_tokens,
)
from ..methodology_transfer.probe_generator import (
    probe_fires,
)
from .enums import RewriteKind
from .raw_corpus import ChainPair


SAFE_PROBE_CLASSES: tuple[str, ...] = (
    "MT_MODAL_ASYMMETRY",
    "MT_NEGATION_ASYMMETRY",
    "MT_UNIVERSAL_LEAP",
    "MT_OVERLAP_LOOP",
    "MT_AUDIT_OVER_SUPPORT",
    "MT_AUDIT_OVER_BLOCK",
)


def _token_edit_distance(a: str, b: str) -> int:
    """Symmetric difference of token multisets — the
    minimum number of single-token insertions and
    deletions to turn one into the other (ignoring
    reordering, which the v5.0 cascade is invariant
    to)."""
    from collections import Counter
    ca = Counter(_all_tokens(a))
    cb = Counter(_all_tokens(b))
    diff = 0
    for tok in set(ca) | set(cb):
        diff += abs(ca.get(tok, 0) - cb.get(tok, 0))
    return diff


def _jaccard(a: str, b: str) -> float:
    ta = _content_tokens(a)
    tb = _content_tokens(b)
    if not ta and not tb:
        return 1.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _probes_firing(text: str) -> set[str]:
    return {p for p in SAFE_PROBE_CLASSES if probe_fires(p, text)}


@dataclass(frozen=True)
class ChainAudit:
    chain_id: str
    domain: str
    ground_truth: str
    was_rewritten: bool
    token_edit_distance: int
    probe_alignment_delta: int
    probe_avoidance_delta: int
    semantic_similarity: float
    label_preservation: bool
    rewrite_kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "ground_truth": self.ground_truth,
            "was_rewritten": self.was_rewritten,
            "token_edit_distance":
                self.token_edit_distance,
            "probe_alignment_delta":
                self.probe_alignment_delta,
            "probe_avoidance_delta":
                self.probe_avoidance_delta,
            "semantic_similarity":
                round(self.semantic_similarity, 6),
            "label_preservation":
                self.label_preservation,
            "rewrite_kind": self.rewrite_kind,
        }


def audit_pair(pair: ChainPair) -> ChainAudit:
    raw_probes = _probes_firing(pair.raw_text)
    final_probes = _probes_firing(pair.final_text)
    alignment = len(final_probes - raw_probes)
    avoidance = len(raw_probes - final_probes)
    sim = _jaccard(pair.raw_text, pair.final_text)
    edit = _token_edit_distance(
        pair.raw_text, pair.final_text,
    )
    # label preservation is structural: the RAW corpus
    # reconstruction never alters ground_truth.
    label_kept = True
    if not pair.was_rewritten:
        kind = RewriteKind.NONE.value
    elif alignment > 0 and avoidance == 0:
        kind = RewriteKind.PROBE_ALIGNMENT.value
    elif avoidance > 0 and alignment == 0:
        kind = RewriteKind.PROBE_AVOIDANCE.value
    else:
        kind = RewriteKind.SEMANTIC_PARAPHRASE.value
    return ChainAudit(
        chain_id=pair.chain_id, domain=pair.domain,
        ground_truth=pair.ground_truth,
        was_rewritten=pair.was_rewritten,
        token_edit_distance=edit,
        probe_alignment_delta=alignment,
        probe_avoidance_delta=avoidance,
        semantic_similarity=sim,
        label_preservation=label_kept,
        rewrite_kind=kind,
    )


__all__ = [
    "ChainAudit", "SAFE_PROBE_CLASSES", "audit_pair",
]
