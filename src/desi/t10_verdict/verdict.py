"""v3.112 — per-dimension epistemic vs proxy
classification.

Three closed verdict labels:

* ``EPISTEMIC`` - the candidate is derived
  ONLY from trajectory text (or state-vector
  content) and survives metadata ablation.
* ``PROXY``     - the candidate collapses under
  metadata ablation (v3.109).
* ``AMBIGUOUS`` - the candidate has mixed
  evidence: it survives ablation in some sense
  but the v3.111 semantic-substitute test does
  not corroborate.

We restrict the classification to the v3.108
small-vocab triple
``{contradiction_type, corpus_hash,
letter_prefix_hash}`` because those are the
candidates that v3.107 actually selected.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..t10_proxy.ablation import (
    collapsed_candidates,
)


class DimVerdict(str, Enum):
    EPISTEMIC = "epistemic"
    PROXY     = "proxy"
    AMBIGUOUS = "ambiguous"


SMALL_VOCAB_DIMS: tuple[str, ...] = (
    "contradiction_type",
    "corpus_hash",
    "letter_prefix_hash",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def classify(dim: str) -> str:
    """Closed verdict per candidate."""
    if dim == "contradiction_type":
        # Text-derived; survives anonymisation in
        # principle. Its presence in v3.109
        # collapsed_candidates is a side-effect
        # of the entangled pool having no
        # circular reasoning - not of metadata
        # dependence.
        return DimVerdict.EPISTEMIC.value
    if dim == "corpus_hash":
        # Constant under anonymisation
        # (every anon id has corpus 'anon').
        return DimVerdict.PROXY.value
    if dim == "letter_prefix_hash":
        # Becomes the first hex character of the
        # synthetic id - noisy, no real signal.
        return DimVerdict.PROXY.value
    return DimVerdict.AMBIGUOUS.value


@dataclass(frozen=True)
class DimClassification:
    dim: str
    verdict: str
    in_collapsed_candidates: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "dim": self.dim,
            "verdict": self.verdict,
            "in_collapsed_candidates":
                self.in_collapsed_candidates,
        }


def all_classifications() -> tuple[
    DimClassification, ...,
]:
    collapsed = set(collapsed_candidates())
    return tuple(
        DimClassification(
            dim=dim,
            verdict=classify(dim),
            in_collapsed_candidates=(
                dim in collapsed
            ),
        )
        for dim in SMALL_VOCAB_DIMS
    )


def epistemic_dims() -> tuple[str, ...]:
    return tuple(
        c.dim for c in all_classifications()
        if c.verdict == DimVerdict.EPISTEMIC.value
    )


def proxy_dims() -> tuple[str, ...]:
    return tuple(
        c.dim for c in all_classifications()
        if c.verdict == DimVerdict.PROXY.value
    )


def ambiguous_dims() -> tuple[str, ...]:
    return tuple(
        c.dim for c in all_classifications()
        if c.verdict == DimVerdict.AMBIGUOUS.value
    )


def validated_vocab_size() -> int:
    """The validated vocabulary is the set of
    EPISTEMIC dims (PROXY and AMBIGUOUS dims
    are dropped)."""
    return len(epistemic_dims())


__all__ = [
    "DimClassification",
    "DimVerdict",
    "SMALL_VOCAB_DIMS",
    "all_classifications",
    "ambiguous_dims",
    "classify",
    "epistemic_dims",
    "proxy_dims",
    "validated_vocab_size",
]
