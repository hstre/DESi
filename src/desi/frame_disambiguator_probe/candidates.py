"""Candidate generation + precision/coverage — Aufgaben 2, 4, 5."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from .extractor import CounterCase, TargetCase


# Tokens we ignore when building combinations — they're frame-marker
# fragments or stopwords that would trivially over-match.
_STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "for", "are", "was", "were", "with", "from",
    "this", "that", "into", "have", "has", "had", "all", "any",
    "but", "not", "its", "may", "can", "will", "shall",
    "frame", "thermodynamic", "information-theoretic",
    "information", "theoretic", "ontological",
    "distinguishability", "metaphorical", "formal", "logic",
    "empirical", "causal", "authority", "tool", "computable",
    "undeclared",
})


# entropy is the polysemy anchor — every candidate must include it.
_ANCHOR: str = "entropy"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    tokens: tuple[str, ...]   # always includes the anchor

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "tokens": list(self.tokens),
        }


@dataclass(frozen=True)
class CandidateScore:
    candidate: Candidate
    hits_on_targets: tuple[str, ...]
    hits_on_counters: tuple[str, ...]
    info_precision: float
    coverage: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "hits_on_targets": list(self.hits_on_targets),
            "hits_on_counters": list(self.hits_on_counters),
            "info_precision": self.info_precision,
            "coverage": self.coverage,
        }


def _eligible_tokens(targets: tuple[TargetCase, ...]) -> tuple[str, ...]:
    """All non-stopword tokens that appear in at least one target
    (excluding the anchor itself), deduped, sorted."""
    pool: set[str] = set()
    for t in targets:
        for tok in t.tokens:
            if tok == _ANCHOR:
                continue
            if tok in _STOPWORDS:
                continue
            if len(tok) < 3:
                continue
            pool.add(tok)
    return tuple(sorted(pool))


def _hits(text: str, tokens: tuple[str, ...]) -> bool:
    low = text.lower()
    return all(tok in low for tok in tokens)


def generate_candidates(
    targets: tuple[TargetCase, ...],
    *,
    max_size: int = 3,
    min_per_size: int = 0,
) -> tuple[Candidate, ...]:
    """Aufgabe 2 — every candidate is anchor + 1 or 2 other tokens
    drawn from target-text vocabulary.
    """
    extras = _eligible_tokens(targets)
    out: list[Candidate] = []

    # size = 2 (anchor + 1)
    for tok in extras:
        toks = (_ANCHOR, tok)
        out.append(Candidate(
            candidate_id="C_" + "_".join(toks),
            tokens=toks,
        ))

    # size = 3 (anchor + 2). We only emit pairs whose joint
    # frequency is high enough to be worth scoring — at least
    # one target text must contain both extras together with
    # the anchor.
    for a, b in combinations(extras, 2):
        toks = (_ANCHOR, a, b)
        present = any(_hits(t.text, toks) for t in targets)
        if present:
            out.append(Candidate(
                candidate_id="C_" + "_".join(toks),
                tokens=toks,
            ))
    return tuple(out)


def score_candidate(
    candidate: Candidate,
    targets: tuple[TargetCase, ...],
    counters: tuple[CounterCase, ...],
) -> CandidateScore:
    target_hits = tuple(
        t.case_id for t in targets if _hits(t.text, candidate.tokens)
    )
    counter_hits = tuple(
        c.source for c in counters if _hits(c.text, candidate.tokens)
    )
    info_total = len(target_hits) + len(counter_hits)
    precision = round(len(target_hits) / info_total, 6) if info_total > 0 else 0.0
    coverage = round(len(target_hits) / len(targets), 6) if targets else 0.0
    return CandidateScore(
        candidate=candidate,
        hits_on_targets=target_hits,
        hits_on_counters=counter_hits,
        info_precision=precision,
        coverage=coverage,
    )


def score_all(
    candidates: tuple[Candidate, ...],
    targets: tuple[TargetCase, ...],
    counters: tuple[CounterCase, ...],
) -> tuple[CandidateScore, ...]:
    return tuple(
        score_candidate(c, targets, counters) for c in candidates
    )


__all__ = [
    "Candidate",
    "CandidateScore",
    "generate_candidates",
    "score_all",
    "score_candidate",
]
