"""v5.1 — synthetic open-world claim sources.

The directive forbids live internet. Each
``ClaimSource`` therefore exposes a closed,
deterministic generator that produces a fixed
fixture of source-flavoured strings. The fixture
is hashed by ``(source, seed, index)`` so it is
identical across replays but varies per seed.

The bodies are intentionally short and use
source-typical idiom (encyclopedic, abstract-y,
issue-y, etc.) so the v5.1 frame classifier can
discriminate sources from text features alone.
"""
from __future__ import annotations

import hashlib
from enum import Enum
from functools import lru_cache


class ClaimSource(str, Enum):
    WIKIPEDIA              = "wikipedia"
    ARXIV                  = "arxiv"
    SSRN                   = "ssrn"
    GITHUB_ISSUE           = "github_issue"
    NEWS                   = "news"
    SYNTHETIC_ADVERSARIAL  = (
        "synthetic_adversarial"
    )


CLAIM_SOURCES: tuple[str, ...] = tuple(
    s.value for s in ClaimSource
)


_SUBJECT_POOL: tuple[str, ...] = (
    "the falsifiability criterion",
    "category theory",
    "the precautionary principle",
    "double-blind review",
    "transformer attention",
    "supply chain attacks",
    "regulatory capture",
    "knowledge graphs",
    "phase transitions",
    "moral hazard",
    "p-value misuse",
    "the Hawthorne effect",
    "open peer review",
    "reproducibility crisis",
    "model collapse",
    "data poisoning",
)


_PREDICATE_POOL: tuple[str, ...] = (
    "is necessary for scientific progress",
    "always fails in practice",
    "should be deprecated by 2030",
    "is a special case of variational inference",
    "predicts collapse within five years",
    "is morally required for funding bodies",
    "cannot exist alongside open science",
    "was misunderstood until the 1980s",
    "is logically equivalent to its negation",
    "produces non-replayable artifacts",
)


_TEMPLATES: dict[str, tuple[str, ...]] = {
    ClaimSource.WIKIPEDIA.value: (
        "{subject} is a concept in epistemology.",
        "{subject}, in the standard definition, "
        "refers to a property of theories.",
    ),
    ClaimSource.ARXIV.value: (
        "We show that {subject} "
        "{predicate}, contradicting prior work.",
        "We prove that {subject} {predicate} "
        "under mild assumptions.",
    ),
    ClaimSource.SSRN.value: (
        "This paper argues that {subject} "
        "{predicate}, with policy implications.",
        "Empirical evidence suggests {subject} "
        "{predicate}.",
    ),
    ClaimSource.GITHUB_ISSUE.value: (
        "BUG: {subject} {predicate} - cannot "
        "reproduce in CI.",
        "feature request: handle the case where "
        "{subject} {predicate}.",
    ),
    ClaimSource.NEWS.value: (
        "Sources confirm: {subject} {predicate}.",
        "Breaking: experts say {subject} "
        "{predicate}.",
    ),
    ClaimSource.SYNTHETIC_ADVERSARIAL.value: (
        "{subject} {predicate} AND {subject} "
        "does not {predicate} - both at once.",
        "Trust me bro: {subject} {predicate} "
        "because reasons.",
    ),
}


def _digest(
    source: str, seed: int, index: int,
) -> bytes:
    raw = (
        f"{source}:{seed}:{index}"
        .encode("utf-8")
    )
    return hashlib.sha256(raw).digest()


def _pick(
    pool: tuple[str, ...], digest: bytes,
    offset: int,
) -> str:
    idx = digest[offset] % len(pool)
    return pool[idx]


def generate_claim(
    source: ClaimSource, seed: int,
    index: int,
) -> str:
    d = _digest(source.value, seed, index)
    templates = _TEMPLATES[source.value]
    tmpl = templates[d[0] % len(templates)]
    subject = _pick(_SUBJECT_POOL, d, 1)
    predicate = _pick(_PREDICATE_POOL, d, 2)
    return tmpl.format(
        subject=subject, predicate=predicate,
    )


@lru_cache(maxsize=None)
def source_claims(
    source: ClaimSource, seed: int, count: int,
) -> tuple[str, ...]:
    return tuple(
        generate_claim(source, seed, i)
        for i in range(count)
    )


__all__ = [
    "CLAIM_SOURCES",
    "ClaimSource",
    "generate_claim",
    "source_claims",
]
