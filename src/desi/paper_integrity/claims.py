"""v13.0 — closed paper-class + claim-kind
taxonomies and a synthetic 5-class fixture.

This module honestly does NOT detect AI style.
It detects EPISTEMIC STRUCTURE: whether a
paper's claims have method-evidence support,
whether bridges are valid, whether limitations
are substantive. Same paper text from a human
or AI exits with the SAME structural verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PaperClass(str, Enum):
    """Closed fixture-class taxonomy per the
    directive."""
    GOLD              = "gold_set"
    WEAK              = "weak_set"
    AI_SLUDGE         = "ai_sludge"
    ADVERSARIAL       = "adversarial_set"
    BORDERLINE        = "borderline_set"


PAPER_CLASSES: tuple[str, ...] = tuple(
    c.value for c in PaperClass
)


class ClaimKind(str, Enum):
    EMPIRICAL    = "empirical"
    CAUSAL       = "causal"
    DEFINITIONAL = "definitional"
    OVERREACH    = "overreach"


CLAIM_KINDS: tuple[str, ...] = tuple(
    k.value for k in ClaimKind
)


@dataclass(frozen=True)
class PaperClaim:
    paper_id: str
    paper_class: str
    claim_text: str
    claim_kind: str
    method_supported: bool
    evidence_supported: bool
    bridge_valid: bool
    references_grounded: bool
    has_substantive_limitations: bool
    has_overclaim: bool
    has_hallucinated_diagram: bool
    has_hallucinated_stats: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "paper_class": self.paper_class,
            "claim_text": self.claim_text,
            "claim_kind": self.claim_kind,
            "method_supported":
                self.method_supported,
            "evidence_supported":
                self.evidence_supported,
            "bridge_valid":
                self.bridge_valid,
            "references_grounded":
                self.references_grounded,
            "has_substantive_limitations": (
                self.has_substantive_limitations
            ),
            "has_overclaim":
                self.has_overclaim,
            "has_hallucinated_diagram":
                self.has_hallucinated_diagram,
            "has_hallucinated_stats":
                self.has_hallucinated_stats,
        }


def _c(
    pid: str, cls: PaperClass, text: str,
    kind: ClaimKind, ms: bool, es: bool,
    bv: bool, rg: bool, lim: bool,
    oc: bool, hd: bool, hs: bool,
) -> PaperClaim:
    return PaperClaim(
        paper_id=pid, paper_class=cls.value,
        claim_text=text, claim_kind=kind.value,
        method_supported=ms,
        evidence_supported=es,
        bridge_valid=bv,
        references_grounded=rg,
        has_substantive_limitations=lim,
        has_overclaim=oc,
        has_hallucinated_diagram=hd,
        has_hallucinated_stats=hs,
    )


_FIXTURE: tuple[PaperClaim, ...] = (
    # GOLD: solid, supported, with honest limits.
    _c("paper-gold-001", PaperClass.GOLD,
       "RCT estimates a 4 percent reduction "
       "in cardiovascular events; CI reported.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
    _c("paper-gold-002", PaperClass.GOLD,
       "Pre-registered replication confirms "
       "the primary outcome; limitations on "
       "external validity noted.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
    # WEAK: honest but underpowered.
    _c("paper-weak-001", PaperClass.WEAK,
       "Pilot study with n=12 suggests a "
       "trend; honest about low power.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
    _c("paper-weak-002", PaperClass.WEAK,
       "Exploratory analysis with wide CI; "
       "authors caveat conclusions.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
    # AI_SLUDGE: hallucinated diagrams/stats,
    # ungrounded references.
    _c("paper-sludge-001",
       PaperClass.AI_SLUDGE,
       "Our novel transformer achieves 99.7 "
       "percent accuracy on benchmark X.",
       ClaimKind.EMPIRICAL,
       ms=False, es=False, bv=False, rg=False,
       lim=False, oc=True, hd=True, hs=True),
    _c("paper-sludge-002",
       PaperClass.AI_SLUDGE,
       "Figure 3 shows that diagram correlations "
       "improve by 42 percent (no figure 3 "
       "actually exists).",
       ClaimKind.EMPIRICAL,
       ms=False, es=False, bv=False, rg=False,
       lim=False, oc=True, hd=True, hs=True),
    # ADVERSARIAL: looks polished, selectively
    # reports, overclaims.
    _c("paper-adv-001", PaperClass.ADVERSARIAL,
       "Therefore mechanism X causes outcome Y "
       "in all populations.",
       ClaimKind.OVERREACH,
       ms=False, es=False, bv=False, rg=True,
       lim=False, oc=True, hd=False, hs=False),
    _c("paper-adv-002", PaperClass.ADVERSARIAL,
       "We report only the benchmark on which "
       "our method wins; null results omitted.",
       ClaimKind.EMPIRICAL,
       ms=True, es=False, bv=False, rg=True,
       lim=False, oc=True, hd=False, hs=False),
    # BORDERLINE: AI-assisted but legit.
    _c("paper-border-001",
       PaperClass.BORDERLINE,
       "Hypothesis drafted with LLM assistance; "
       "RCT data and analysis pre-registered; "
       "limits stated.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
    _c("paper-border-002",
       PaperClass.BORDERLINE,
       "Section 4 was machine-edited for "
       "clarity; methods and data are human-"
       "verified and reproducible.",
       ClaimKind.EMPIRICAL,
       ms=True, es=True, bv=True, rg=True,
       lim=True, oc=False, hd=False, hs=False),
)


def fixture() -> tuple[PaperClaim, ...]:
    return _FIXTURE


def class_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.paper_class for c in fixture()
    ))


__all__ = [
    "CLAIM_KINDS",
    "ClaimKind",
    "PAPER_CLASSES",
    "PaperClaim",
    "PaperClass",
    "class_counts",
    "fixture",
]
