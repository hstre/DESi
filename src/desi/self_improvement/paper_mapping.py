"""v28.0 - map research signals to improvement provenance.

Resolves a candidate's source (an open-question claim in the v27
research corpus) back to its paper, so every improvement
candidate keeps an explicit, checkable provenance chain. This
module only reads the corpus; it proposes nothing.
"""
from __future__ import annotations

from desi.research_harvester import all_claims
from desi.research_harvester.taxonomy import ClaimClass as K


def _claim_index() -> dict[str, str]:
    return {c.claim_id: c.paper_id for c in all_claims()}


def is_valid_source(claim_id: str) -> bool:
    return claim_id in _claim_index()


def source_paper_of(claim_id: str) -> str:
    idx = _claim_index()
    if claim_id not in idx:
        raise KeyError(claim_id)
    return idx[claim_id]


def open_question_ids() -> tuple[str, ...]:
    return tuple(sorted(
        c.claim_id for c in all_claims()
        if c.claim_class == K.OPEN_QUESTION.value
    ))


__all__ = [
    "is_valid_source",
    "open_question_ids",
    "source_paper_of",
]
