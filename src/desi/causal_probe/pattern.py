"""CausalChainCandidate + hypothetical trigger — Aufgaben 2 + 4.

A pure data structure plus a deterministic *hypothetical* trigger.
The trigger is intentionally a paper exercise — it never runs in
production, never feeds a resolver, never affects a benchmark run.
It exists solely to answer: "**if** such a rule existed, which
cases would it fire on?"

No regex is used; only Python string operations.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..recursive import ResolutionState
from .risk import RiskFlag


class BenchmarkSource(str, Enum):
    MAIN_50 = "main_50"
    MULTISTEP_30 = "multistep_30"


@dataclass(frozen=True)
class CausalChainCandidate:
    """Read-only probe of one case (Aufgabe 2)."""

    case_id: str
    benchmark_source: BenchmarkSource
    text: str
    premise_count: int
    therefore_count: int
    atomic_sequence: int
    repeated_subjects: int
    repeated_predicates: int
    candidate_triggered: bool
    trigger_reason: str
    risk_flags: tuple[RiskFlag, ...]
    expected_label: str
    current_final_state: ResolutionState
    replay_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "benchmark_source": self.benchmark_source.value,
            "text": self.text,
            "premise_count": self.premise_count,
            "therefore_count": self.therefore_count,
            "atomic_sequence": self.atomic_sequence,
            "repeated_subjects": self.repeated_subjects,
            "repeated_predicates": self.repeated_predicates,
            "candidate_triggered": self.candidate_triggered,
            "trigger_reason": self.trigger_reason,
            "risk_flags": [f.value for f in self.risk_flags],
            "expected_label": self.expected_label,
            "current_final_state": self.current_final_state.value,
            "replay_hash": self.replay_hash,
        }


# ---------------------------------------------------------------------------
# Text utilities (no regex)
# ---------------------------------------------------------------------------


_STOPWORDS: frozenset[str] = frozenset({
    # determiners / pronouns
    "the", "a", "an", "this", "that", "these", "those",
    "it", "they", "he", "she", "we", "you", "i",
    # connectors / discourse
    "therefore", "thus", "so", "hence", "and", "or", "but",
    "because", "since", "if", "then", "than", "as",
    # to be / aux
    "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    # common prepositions
    "of", "in", "on", "at", "to", "for", "with", "without",
    "by", "from", "into", "over", "under",
    # misc fillers
    "not", "no", "yes", "all", "some", "any", "more", "less",
    "very", "much", "many", "few",
})


def _count_substring(text: str, needle: str) -> int:
    """Case-insensitive non-overlapping substring count."""
    lo = text.lower()
    n = 0
    start = 0
    while True:
        i = lo.find(needle, start)
        if i < 0:
            break
        n += 1
        start = i + len(needle)
    return n


def _sentences(text: str) -> list[str]:
    """Naïve sentence split on '. '/'? ' — no regex."""
    cleaned = text.replace("?", ".")
    parts = cleaned.split(". ")
    return [p.strip(" .") for p in parts if p.strip(" .")]


def _content_tokens(sentence: str) -> set[str]:
    """Lowercase content-word set; punctuation stripped."""
    s = sentence.lower()
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    out: set[str] = set()
    for tok in s.split():
        if tok in _STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        out.add(tok)
    return out


def count_repeated_content(text: str) -> tuple[int, int]:
    """Return (repeated_subjects, repeated_predicates).

    Heuristic-free approximation: a content token that appears in
    two adjacent sentences counts toward ``repeated_subjects`` if it
    is the *first* shared token, ``repeated_predicates`` otherwise.
    The two counters are observation, not rule-fodder.
    """
    sents = _sentences(text)
    subj = 0
    pred = 0
    for a, b in zip(sents, sents[1:]):
        shared = _content_tokens(a) & _content_tokens(b)
        if not shared:
            continue
        # Sort for determinism, take the first as the "subject"
        # axis, count the rest as predicate-axis repetitions.
        ordered = sorted(shared)
        subj += 1
        pred += len(ordered) - 1
    return subj, pred


def count_atomic_sequence(premise_kinds: tuple[str, ...]) -> int:
    """Longest run of consecutive atomic/particular premise kinds."""
    atomic_like = {"atomic", "particular"}
    longest = 0
    run = 0
    for k in premise_kinds:
        if k in atomic_like:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest


# ---------------------------------------------------------------------------
# Hypothetical trigger
# ---------------------------------------------------------------------------


def hypothetical_trigger(
    *,
    premise_count: int,
    therefore_count: int,
    atomic_sequence: int,
) -> tuple[bool, str]:
    """Aufgabe 4 — paper-only trigger.

    Returns ``(triggered, reason)``. The trigger never feeds any
    resolver; it exists to enumerate cases a future CAUSAL_CHAIN
    rule **could** match if implemented.
    """
    if therefore_count < 1:
        return False, "therefore_count < 1"
    if premise_count < 1:
        return False, "premise_count < 1"
    if atomic_sequence < 2:
        return False, "atomic_sequence < 2"
    return True, (
        f"therefore_count={therefore_count}, "
        f"premise_count={premise_count}, "
        f"atomic_sequence={atomic_sequence}"
    )


# ---------------------------------------------------------------------------
# Replay hash helper
# ---------------------------------------------------------------------------


def candidate_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items() if k != "replay_hash"}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "BenchmarkSource",
    "CausalChainCandidate",
    "candidate_replay_hash",
    "count_atomic_sequence",
    "count_repeated_content",
    "hypothetical_trigger",
]
