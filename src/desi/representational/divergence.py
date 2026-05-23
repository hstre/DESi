"""v3.97 — structural concept divergence.

While ``semantic_loss`` measures vocabulary
overlap, this module measures **structural
concept** divergence: does each family follow a
distinct reasoning template?

Closed concept taxonomy:

* ``CIRCULAR_REASONING`` - "X PRED Y. Y PRED X.
  Therefore ..." pattern (G_v316susp).
* ``UNIVERSAL_SYLLOGISM`` - "All / Every X ...
  Therefore ..." pattern (E_v317h subset).
* ``POST_HOC_NARRATIVE`` - two factual sentences
  followed by "Therefore ..." with no universal
  quantifier and no circular structure (E_v317h
  subset).
* ``UNCLASSIFIED`` - none of the above.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..novel_families import all_family_members


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


class ConceptKind(str, Enum):
    CIRCULAR_REASONING  = "circular_reasoning"
    UNIVERSAL_SYLLOGISM = "universal_syllogism"
    POST_HOC_NARRATIVE  = "post_hoc_narrative"
    UNCLASSIFIED        = "unclassified"


_CIRCULAR_PREDICATES: tuple[str, ...] = (
    "rests on", "rest on",
    "follows from", "follow from",
    "leans against", "lean against",
    "stems from", "stem from",
    "comes from", "come from",
    "stands on", "stand on",
    "emerges from", "emerge from",
    "grows from", "grow from",
)


_UNIVERSAL_OPENERS: tuple[str, ...] = (
    "all ", "every ", "some ", "any ",
)


_THEREFORE: str = "therefore"


def _split_sentences(text: str) -> tuple[str, ...]:
    raw = re.split(r"[.!?]+", text)
    return tuple(s.strip() for s in raw if s.strip())


def _has_circular_pair(text: str) -> bool:
    """True iff the text contains two sentences
    that share a predicate but have swapped
    subject/object. The detection is conservative:
    we look for a closed predicate phrase that
    appears twice in the text."""
    low = text.lower()
    for pred in _CIRCULAR_PREDICATES:
        if low.count(pred) >= 2:
            # Same predicate appears in two
            # sentences; this is the circular
            # marker.
            return True
    return False


def _has_universal_quantifier(text: str) -> bool:
    low = text.lower().strip()
    if any(low.startswith(opener)
           for opener in _UNIVERSAL_OPENERS):
        return True
    # Also accept "All / Every" appearing at the
    # start of any sentence (not just the first).
    for s in _split_sentences(text):
        slow = s.lower()
        if any(
            slow.startswith(opener)
            for opener in _UNIVERSAL_OPENERS
        ):
            return True
    return False


def _has_therefore(text: str) -> bool:
    return _THEREFORE in text.lower()


def classify_text(text: str) -> str:
    has_circle = _has_circular_pair(text)
    has_universal = _has_universal_quantifier(text)
    has_therefore = _has_therefore(text)
    if has_circle and has_therefore:
        return ConceptKind.CIRCULAR_REASONING.value
    if has_universal and has_therefore:
        return ConceptKind.UNIVERSAL_SYLLOGISM.value
    if (
        not has_circle
        and not has_universal
        and has_therefore
    ):
        return ConceptKind.POST_HOC_NARRATIVE.value
    return ConceptKind.UNCLASSIFIED.value


@dataclass(frozen=True)
class ConceptAssignment:
    trajectory_id: str
    family_id: str
    text: str
    concept: str

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "family_id": self.family_id,
            "text": self.text,
            "concept": self.concept,
        }


@lru_cache(maxsize=1)
def all_concept_assignments() -> tuple[
    ConceptAssignment, ...,
]:
    fams = all_family_members()
    members = set(entangled_members())
    out: list[ConceptAssignment] = []
    for t in extract_all_trajectories():
        if t.trajectory_id not in members:
            continue
        family_id = "?"
        for fid, ms in fams.items():
            if (
                fid in ENTANGLED_FAMILY_IDS
                and t.trajectory_id in ms
            ):
                family_id = fid
                break
        out.append(ConceptAssignment(
            trajectory_id=t.trajectory_id,
            family_id=family_id,
            text=t.text,
            concept=classify_text(t.text),
        ))
    return tuple(sorted(
        out, key=lambda c: c.trajectory_id,
    ))


def concept_distribution_by_family() -> dict[
    str, dict[str, int],
]:
    out: dict[str, dict[str, int]] = {
        fid: {k.value: 0 for k in ConceptKind}
        for fid in ENTANGLED_FAMILY_IDS
    }
    for c in all_concept_assignments():
        if c.family_id in out:
            out[c.family_id][c.concept] += 1
    return out


def concept_divergence() -> float:
    """Total-variation distance between the two
    families' concept distributions. 0 = identical
    concept mix, 1 = fully disjoint."""
    dist = concept_distribution_by_family()
    a_id, b_id = ENTANGLED_FAMILY_IDS
    a_total = sum(dist[a_id].values()) or 1
    b_total = sum(dist[b_id].values()) or 1
    tv = 0.0
    for k in ConceptKind:
        a_p = dist[a_id][k.value] / a_total
        b_p = dist[b_id][k.value] / b_total
        tv += abs(a_p - b_p)
    return _round(tv / 2.0)


def dominant_concept_per_family() -> dict[str, str]:
    out: dict[str, str] = {}
    dist = concept_distribution_by_family()
    for fid, counts in dist.items():
        if not any(counts.values()):
            out[fid] = ConceptKind.UNCLASSIFIED.value
            continue
        out[fid] = max(
            counts.items(),
            key=lambda kv: (kv[1], kv[0]),
        )[0]
    return out


__all__ = [
    "ConceptAssignment",
    "ConceptKind",
    "all_concept_assignments",
    "classify_text",
    "concept_distribution_by_family",
    "concept_divergence",
    "dominant_concept_per_family",
]
