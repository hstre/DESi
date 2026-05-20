"""v23.3 - simulated base-paper-author review.

Stress-tests the follow-up against the two ways an author
dismisses an unsolicited follow-up: as spam (generic, not
connected to their work) or as hype (overclaiming, inflated).
Each probe is resolved from a real lower-layer signal, so the
spam / hype probabilities are measured, not asserted.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_followup_revision import (
    addresses_section_4_6, generic_claim_reduction,
)
from desi.icrl_followup_density import (
    claim_conservatism, corpus_forbidden_hits,
    hypothesis_visibility,
)

from .disconnect_detection import paper_connection_visibility

SPAM = "spam"
HYPE = "hype"
DISMISSAL_CLASSES: tuple[str, ...] = (SPAM, HYPE)

VERDICT_RELEVANT = "AUTHOR_WOULD_ENGAGE"
VERDICT_DISMISSED = "AUTHOR_WOULD_DISMISS"


@dataclass(frozen=True)
class ReviewProbe:
    probe_id: str
    question: str
    dismissal_class: str
    passed: bool
    reaction: str

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "question": self.question,
            "dismissal_class": self.dismissal_class,
            "passed": self.passed,
            "reaction": self.reaction,
        }


def _probes() -> tuple[ReviewProbe, ...]:
    cites_section = addresses_section_4_6()
    specific = generic_claim_reduction() >= 0.90
    connected = paper_connection_visibility() >= 0.90
    no_forbidden = not corpus_forbidden_hits()
    conservative = claim_conservatism() >= 0.90
    hyp_marked = hypothesis_visibility() >= 0.90
    return (
        ReviewProbe(
            "PR1",
            "Does it cite Section 4.6 of my paper?",
            SPAM, cites_section,
            "It points straight at my open exploration "
            "problem, so it is not a generic mailing."),
        ReviewProbe(
            "PR2",
            "Is it specific rather than generic boilerplate?",
            SPAM, specific,
            "The claims are specific to my setting, not "
            "reusable filler."),
        ReviewProbe(
            "PR3",
            "Do the claims connect to my open problems?",
            SPAM, connected,
            "Each claim names the problem it addresses, so it "
            "reads as a real follow-up."),
        ReviewProbe(
            "PR4",
            "Does it avoid inflated buzzwords?",
            HYPE, no_forbidden,
            "No inflated terminology appears, so it does not "
            "read as a hype pitch."),
        ReviewProbe(
            "PR5",
            "Does it avoid overclaiming beyond the sandbox?",
            HYPE, conservative,
            "Significance is scoped to the synthetic corpus, "
            "which I trust more than a sweeping claim."),
        ReviewProbe(
            "PR6",
            "Are speculations marked as hypotheses?",
            HYPE, hyp_marked,
            "Forward-looking statements are flagged as open "
            "hypotheses, not sold as results."),
    )


def review_probes() -> tuple[ReviewProbe, ...]:
    return _probes()


def failing_probes() -> tuple[str, ...]:
    return tuple(p.probe_id for p in _probes() if not p.passed)


def _class_probability(klass: str) -> float:
    rows = [p for p in _probes() if p.dismissal_class == klass]
    if not rows:
        return 0.0
    failed = sum(1 for p in rows if not p.passed)
    return round(failed / len(rows), 6)


def spam_probability() -> float:
    """Estimated probability the author files the follow-up as
    spam, in [0, 1] (fraction of spam-type probes that fail)."""
    return _class_probability(SPAM)


def hype_probability() -> float:
    """Estimated probability the author dismisses the follow-up
    as hype, in [0, 1] (fraction of hype-type probes failing)."""
    return _class_probability(HYPE)


def simulated_verdict() -> str:
    return (
        VERDICT_RELEVANT if not failing_probes()
        else VERDICT_DISMISSED
    )


__all__ = [
    "DISMISSAL_CLASSES",
    "HYPE",
    "SPAM",
    "VERDICT_DISMISSED",
    "VERDICT_RELEVANT",
    "ReviewProbe",
    "failing_probes",
    "hype_probability",
    "review_probes",
    "simulated_verdict",
    "spam_probability",
]
