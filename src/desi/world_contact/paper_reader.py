"""v6.0 — synthetic-but-realistic paper corpus.

The directive lists arXiv / SSRN / PubMed / ACL
/ Nature as candidate sources. Live internet is
forbidden by the sandbox rules, so the corpus is
a closed fixture of paper-shaped objects whose
abstracts imitate the structure of real venue
output (citation idiom, hedging, claim
patterns). Every paper carries a closed ground
truth that the v6.0 audit grades itself against.

Each paper has:

* ``paper_id``       - stable identifier
* ``venue``          - one of the closed venues
* ``title`` / ``abstract`` - the body text
* ``stated_claims``  - claims the audit MUST
                       extract (positive ground
                       truth)
* ``unsupported_leaps`` - claims that overreach
                          the evidence (the
                          auditor MUST flag them)
* ``valid_bridges``  - explicit bridge phrases
                       in the abstract that
                       license the claims
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class Venue(str, Enum):
    ARXIV    = "arxiv"
    SSRN     = "ssrn"
    PUBMED   = "pubmed"
    ACL      = "acl"
    NATURE   = "nature"


VENUES: tuple[str, ...] = tuple(
    v.value for v in Venue
)


@dataclass(frozen=True)
class Paper:
    paper_id: str
    venue: str
    title: str
    abstract: str
    stated_claims: tuple[str, ...]
    unsupported_leaps: tuple[str, ...]
    valid_bridges: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "venue": self.venue,
            "title": self.title,
            "abstract": self.abstract,
            "stated_claims":
                list(self.stated_claims),
            "unsupported_leaps":
                list(self.unsupported_leaps),
            "valid_bridges":
                list(self.valid_bridges),
        }


_CORPUS: tuple[Paper, ...] = (
    Paper(
        paper_id="arxiv:2401.0001",
        venue=Venue.ARXIV.value,
        title=(
            "Convergence of attention-based "
            "language models under sparse "
            "supervision"
        ),
        abstract=(
            "We show that attention-based "
            "language models converge to a "
            "stable representation under "
            "sparse supervision. Empirical "
            "evidence on three benchmark "
            "datasets supports the claim. We "
            "further argue that this implies "
            "general intelligence."
        ),
        stated_claims=(
            "attention-based language models "
            "converge to a stable "
            "representation under sparse "
            "supervision",
        ),
        unsupported_leaps=(
            "this implies general intelligence",
        ),
        valid_bridges=(
            "empirical evidence on three "
            "benchmark datasets supports the "
            "claim",
        ),
    ),
    Paper(
        paper_id="ssrn:2024-4501",
        venue=Venue.SSRN.value,
        title=(
            "Regulatory disclosure and market "
            "efficiency"
        ),
        abstract=(
            "This paper argues that mandatory "
            "regulatory disclosure improves "
            "market efficiency. Empirical "
            "evidence suggests a 12 percent "
            "reduction in bid-ask spreads "
            "after the 2018 reform. We "
            "conclude that disclosure is "
            "morally required."
        ),
        stated_claims=(
            "mandatory regulatory disclosure "
            "improves market efficiency",
            "a 12 percent reduction in bid-ask "
            "spreads after the 2018 reform",
        ),
        unsupported_leaps=(
            "disclosure is morally required",
        ),
        valid_bridges=(),
    ),
    Paper(
        paper_id="pubmed:38901234",
        venue=Venue.PUBMED.value,
        title=(
            "Vitamin D supplementation and "
            "cardiovascular outcomes"
        ),
        abstract=(
            "Randomised controlled trial of "
            "Vitamin D supplementation in "
            "elderly cohort. We show that "
            "Vitamin D reduces the relative "
            "risk of cardiovascular events by "
            "8 percent. This proves that "
            "Vitamin D prevents heart disease."
        ),
        stated_claims=(
            "Vitamin D reduces the relative "
            "risk of cardiovascular events by "
            "8 percent",
        ),
        unsupported_leaps=(
            "this proves that Vitamin D "
            "prevents heart disease",
        ),
        valid_bridges=(
            "randomised controlled trial",
        ),
    ),
    Paper(
        paper_id="acl:2024.naacl.117",
        venue=Venue.ACL.value,
        title=(
            "Cross-lingual transfer in low-"
            "resource morphology"
        ),
        abstract=(
            "We prove that cross-lingual "
            "transfer improves morphological "
            "tagging accuracy on five low-"
            "resource languages. Empirical "
            "evidence suggests the gain is "
            "robust to typological distance. "
            "Trust me bro: this generalises "
            "to all languages."
        ),
        stated_claims=(
            "cross-lingual transfer improves "
            "morphological tagging accuracy "
            "on five low-resource languages",
        ),
        unsupported_leaps=(
            "trust me bro: this generalises "
            "to all languages",
        ),
        valid_bridges=(),
    ),
    Paper(
        paper_id="nature:2024.05.789",
        venue=Venue.NATURE.value,
        title=(
            "Phase transition in superconducting "
            "magnesium diboride"
        ),
        abstract=(
            "We report a phase transition in "
            "magnesium diboride at 39 Kelvin, "
            "consistent with phonon-mediated "
            "pairing. Empirical evidence "
            "supports the BCS mechanism."
        ),
        stated_claims=(
            "a phase transition in magnesium "
            "diboride at 39 Kelvin",
            "consistent with phonon-mediated "
            "pairing",
        ),
        unsupported_leaps=(),
        valid_bridges=(
            "empirical evidence supports",
        ),
    ),
    Paper(
        paper_id="arxiv:2402.0042",
        venue=Venue.ARXIV.value,
        title=(
            "Failure modes of speculative "
            "decoding"
        ),
        abstract=(
            "BUG: speculative decoding fails "
            "silently on long-context inputs - "
            "cannot reproduce in CI. We show "
            "that the failure rate exceeds 4 "
            "percent on the validation set. "
            "Sources confirm the regression."
        ),
        stated_claims=(
            "the failure rate exceeds 4 "
            "percent on the validation set",
        ),
        unsupported_leaps=(
            "sources confirm the regression",
        ),
        valid_bridges=(),
    ),
)


@lru_cache(maxsize=1)
def corpus() -> tuple[Paper, ...]:
    return _CORPUS


def paper_by_id(pid: str) -> Paper:
    for p in corpus():
        if p.paper_id == pid:
            return p
    raise KeyError(pid)


def venue_counts() -> dict[str, int]:
    from collections import Counter
    cnt = Counter(p.venue for p in corpus())
    return {k: cnt[k] for k in sorted(cnt)}


__all__ = [
    "Paper",
    "VENUES",
    "Venue",
    "corpus",
    "paper_by_id",
    "venue_counts",
]
