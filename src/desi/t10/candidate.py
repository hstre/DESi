"""v3.101 — closed candidate-dimension taxonomy.

T10 (representational expansion trigger) admits
EXACTLY ONE additional state dimension. Per the
directive, the audit enumerates a closed set of
candidate dimensions, each derived deterministically
from the trajectory's raw text (no LLM, no external
features beyond the existing extractor).

Closed candidate enum:

* ``REASONING_PATTERN_ID``    - integer code for
  the v3.97 ConceptKind (circular/universal/
  post_hoc/unclassified).
* ``PREMISE_DEPENDENCY``     - count of premise
  sentences before the "Therefore" marker.
* ``INFERENCE_TEMPLATE``     - hash bucket
  derived from the sentence structure
  (subject-predicate-object skeleton).
* ``CONTRADICTION_TYPE``     - whether the text
  contains an explicit self-referential
  contradiction (G's circular structure).
* ``SEMANTIC_OPERATOR_FAMILY`` - the predicate
  family used (rests/follows/leans vs. all/every/
  some).
* ``CLAIM_STRUCTURE_HASH``   - 4-bit sha256
  digest of the lower-cased, punctuation-
  normalised first sentence.

Each candidate maps every entangled-pair anchor
to a single float, which we then append as a
hypothetical 46th coordinate.
"""
from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache
from hashlib import sha256

from ..entangled.variance import (
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..representational.divergence import (
    ConceptKind, classify_text,
)


class CandidateDim(str, Enum):
    REASONING_PATTERN_ID    = "reasoning_pattern_id"
    PREMISE_DEPENDENCY      = "premise_dependency"
    INFERENCE_TEMPLATE      = "inference_template"
    CONTRADICTION_TYPE      = "contradiction_type"
    SEMANTIC_OPERATOR_FAMILY = (
        "semantic_operator_family"
    )
    CLAIM_STRUCTURE_HASH    = "claim_structure_hash"


CANDIDATE_DIMS: tuple[str, ...] = tuple(
    c.value for c in CandidateDim
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_CONCEPT_CODE: dict[str, int] = {
    ConceptKind.CIRCULAR_REASONING.value:  0,
    ConceptKind.UNIVERSAL_SYLLOGISM.value: 1,
    ConceptKind.POST_HOC_NARRATIVE.value:  2,
    ConceptKind.UNCLASSIFIED.value:        3,
}


def _reasoning_pattern_id(text: str) -> float:
    return float(_CONCEPT_CODE[classify_text(text)])


def _premise_dependency(text: str) -> float:
    """Count of sentences before the 'Therefore'
    marker. Pure structural surrogate."""
    low = text.lower()
    if "therefore" not in low:
        return float(
            len(
                [
                    s for s in
                    re.split(r"[.!?]+", text)
                    if s.strip()
                ],
            ),
        )
    head = low.split("therefore", 1)[0]
    sentences = [
        s for s in re.split(r"[.!?]+", head)
        if s.strip()
    ]
    return float(len(sentences))


_INFERENCE_KEYS: tuple[str, ...] = (
    "rests", "follows", "leans", "stems",
    "comes", "stands", "emerges", "grows",
    "all", "every", "some", "any",
)


def _inference_template(text: str) -> float:
    """Bucket index of the first inference keyword
    seen in the text (lower-cased). -1 if none."""
    low = " " + text.lower() + " "
    for i, key in enumerate(_INFERENCE_KEYS):
        if f" {key} " in low:
            return float(i)
    return -1.0


def _contradiction_type(text: str) -> float:
    """1.0 if the text contains an explicit
    self-referential contradiction (a circular
    predicate pair); 0.0 otherwise."""
    low = text.lower()
    pairs = (
        "rests on", "follows from", "leans against",
        "stems from", "comes from", "stands on",
        "emerges from", "grows from",
    )
    return float(
        any(low.count(p) >= 2 for p in pairs),
    )


_OPERATOR_FAMILIES: tuple[tuple[str, ...], ...] = (
    ("rests", "follows", "leans", "stems",
     "comes", "stands", "emerges", "grows"),
    ("all", "every", "some", "any"),
    ("caused", "led to", "results in",
     "stood", "purred", "trained", "flashed",
     "trained", "filled", "attracted"),
)


def _semantic_operator_family(text: str) -> float:
    """Index of the first matching family from
    the closed taxonomy; -1 if no match."""
    low = " " + text.lower() + " "
    for i, family in enumerate(_OPERATOR_FAMILIES):
        for key in family:
            if f" {key} " in low:
                return float(i)
    return -1.0


def _claim_structure_hash(text: str) -> float:
    """First sentence sha256 -> 4-bit bucket."""
    low = text.lower()
    first = re.split(r"[.!?]+", low)[0].strip()
    digest = sha256(first.encode("utf-8")).digest()
    return float(digest[0] & 0x0F)


_CANDIDATE_FNS: dict[str, "callable"] = {
    CandidateDim.REASONING_PATTERN_ID.value:
        _reasoning_pattern_id,
    CandidateDim.PREMISE_DEPENDENCY.value:
        _premise_dependency,
    CandidateDim.INFERENCE_TEMPLATE.value:
        _inference_template,
    CandidateDim.CONTRADICTION_TYPE.value:
        _contradiction_type,
    CandidateDim.SEMANTIC_OPERATOR_FAMILY.value:
        _semantic_operator_family,
    CandidateDim.CLAIM_STRUCTURE_HASH.value:
        _claim_structure_hash,
}


@lru_cache(maxsize=1)
def _entangled_texts() -> dict[str, str]:
    members = set(entangled_members())
    return {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
        if t.trajectory_id in members
    }


@lru_cache(maxsize=None)
def candidate_values(
    candidate: str,
) -> dict[str, float]:
    fn = _CANDIDATE_FNS[candidate]
    return {
        tid: fn(text)
        for tid, text in _entangled_texts().items()
    }


__all__ = [
    "CANDIDATE_DIMS",
    "CandidateDim",
    "candidate_values",
]
