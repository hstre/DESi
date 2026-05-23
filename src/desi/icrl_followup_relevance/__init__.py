"""DESi v23.3 - Targeted ICRL Follow-Up: Author-Relevance
Stress Test (read-only).

Stress-tests whether a base-paper author would recognise the
follow-up as directly continuing their open exploration
question (Section 4.6) - or click it away as spam or hype.
Every signal is read from the v23.0-v23.2 layers, so author
relevance, paper-connection visibility and the spam / hype
dismissal probabilities are measured rather than asserted.
"""
from __future__ import annotations

from .disconnect_detection import (
    ConnectionNote, connection_notes, disconnected_claims,
    paper_connection_visibility,
)
from .interest_model import (
    AuthorInterest, author_interests, interest_topics,
)
from .relevance import author_relevance, unmet_interests
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_IGNORED,
    VERDICT_RELEVANT, V233Report, build_relevance_artifact,
    build_report, corpus_forbidden_hits, relevance_section,
)
from .review_simulation import (
    DISMISSAL_CLASSES, HYPE, SPAM, ReviewProbe, failing_probes,
    hype_probability, review_probes, simulated_verdict,
    spam_probability,
)


__all__ = [
    "DISMISSAL_CLASSES",
    "HYPE",
    "REPORT_VERDICTS",
    "SPAM",
    "VERDICT_HALT",
    "VERDICT_IGNORED",
    "VERDICT_RELEVANT",
    "AuthorInterest",
    "ConnectionNote",
    "ReviewProbe",
    "V233Report",
    "author_interests",
    "author_relevance",
    "build_relevance_artifact",
    "build_report",
    "connection_notes",
    "corpus_forbidden_hits",
    "disconnected_claims",
    "failing_probes",
    "hype_probability",
    "interest_topics",
    "paper_connection_visibility",
    "relevance_section",
    "review_probes",
    "simulated_verdict",
    "spam_probability",
    "unmet_interests",
]
