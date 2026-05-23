"""v23.2 - conservative significance statements.

States why the results matter while staying scoped. A
statement is conservative iff it carries an explicit scope
marker (synthetic / sandbox / corpus / baseline / read-only /
complementary ...) and contains no overclaim token (universal,
global, guarantees, solves, ...). Overclaiming counts against
the metric.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Scope markers that bound a claim to the sandbox / corpus.
_SCOPE_MARKERS: tuple[str, ...] = (
    "synthetic", "sandbox", "corpus", "baseline", "relative",
    "fixture", "scoped", "read-only", "complementary",
    "this setting",
)

# Single-word overclaim tokens (word-boundary matched so
# "solves" does not trip inside "unresolved" etc.).
_OVERCLAIM_WORDS: tuple[str, ...] = (
    "universal", "global", "always", "guarantee",
    "guarantees", "guaranteed", "solves", "solved", "proves",
    "proven", "definitive", "best", "outperforms",
)

# Multi-word / hyphenated overclaim phrases (substring).
_OVERCLAIM_PHRASES: tuple[str, ...] = (
    "any environment", "all environments", "general-purpose",
    "state-of-the-art",
)


def overclaim_hits(text: str) -> tuple[str, ...]:
    low = text.lower()
    hits: list[str] = []
    for w in _OVERCLAIM_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", low):
            hits.append(w)
    for p in _OVERCLAIM_PHRASES:
        if p in low:
            hits.append(p)
    return tuple(hits)


def has_scope_marker(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _SCOPE_MARKERS)


@dataclass(frozen=True)
class SignificanceStatement:
    statement_id: str
    text: str

    def is_conservative(self) -> bool:
        return has_scope_marker(self.text) and not (
            overclaim_hits(self.text)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "statement_id": self.statement_id,
            "text": self.text,
            "is_conservative": self.is_conservative(),
        }


_STATEMENTS: tuple[SignificanceStatement, ...] = (
    SignificanceStatement(
        "S1",
        "Relative to the DESi-only baseline, controlled wild "
        "exploration raised distinct-state coverage on the "
        "synthetic corpus without breaking replay stability."),
    SignificanceStatement(
        "S2",
        "Within this sandbox, a read-only governance layer "
        "kept exploration diverse while down-weighting "
        "redundant search."),
    SignificanceStatement(
        "S3",
        "These results are scoped to synthetic fixtures and "
        "describe a complementary governance layer, not a "
        "substitute for reinforcement learning."),
    SignificanceStatement(
        "S4",
        "The contribution is methodological: the setup is "
        "auditable and replay-exact on the corpus, which is "
        "what we claim and nothing beyond it."),
)


def significance_statements() -> tuple[SignificanceStatement, ...]:
    return _STATEMENTS


def overclaimed_statements() -> tuple[str, ...]:
    return tuple(
        s.statement_id for s in _STATEMENTS
        if not s.is_conservative()
    )


def claim_conservatism() -> float:
    """Fraction of significance statements that are scoped and
    free of overclaim tokens, in [0, 1]."""
    rows = _STATEMENTS
    if not rows:
        return 0.0
    conservative = sum(
        1 for s in rows if s.is_conservative()
    )
    return round(conservative / len(rows), 6)


__all__ = [
    "SignificanceStatement",
    "claim_conservatism",
    "has_scope_marker",
    "overclaim_hits",
    "overclaimed_statements",
    "significance_statements",
]
