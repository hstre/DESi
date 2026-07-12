"""Five epistemic failure modes a scientific "background reviewer" must catch.

Motivation. Claude Science ships "a background reviewer [that] flags incorrect
citations, untraceable numbers, and figures that don't match their underlying
code" and promises artifacts that "ship with their history". That is exactly the
territory the MarCognity / Muse Spark case study mapped — and the case study's whole
point is that an LLM reviewer with retrieval context but WITHOUT source-gating and
provenance binding "verifies" domain-mismatched claims and reads its own failure as
confirmation. So the case study doubles as a **red-team benchmark**: given a
reviewer, does it catch the five failure modes below?

Each probe is anchored to the frozen material (``source_material``) and tied to the
parent case study's own claims, so the benchmark is not a new special-case fixture —
it reuses the analysis that already exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Flag(str, Enum):
    """What a competent reviewer must raise. A reviewer's output is a set of these."""

    UNTRACEABLE_CITATION = "untraceable_citation"        # "verified" with no nameable source/passage
    SOURCE_DOMAIN_MISMATCH = "source_domain_mismatch"    # evidence from the wrong domain
    SELF_SEALING = "self_sealing"                        # every outcome confirms; no falsifier
    OVERCLAIM = "overclaim"                              # conclusion exceeds the evidence (n=1 → "intrinsic")
    HEURISTIC_NOT_EMPIRICAL = "heuristic_not_empirical"  # a construction presented as a measured result


@dataclass(frozen=True)
class Probe:
    """One red-team item: a snippet + the flag a competent reviewer must raise."""

    key: str
    failure_mode: Flag
    title: str
    source_anchor: str          # doc:line into the frozen material
    claim_ids: tuple[str, ...]  # the parent case-study claims this draws on
    snippet: str                # verbatim-ish excerpt under review
    must_flag: Flag
    what_a_reviewer_must_say: str


PROBES: tuple[Probe, ...] = (
    Probe(
        "P1-untraceable",
        Flag.UNTRACEABLE_CITATION,
        "Claims 'VERIFIED' with no nameable source or passage",
        "muse:L170-202",
        ("VAL-01", "VAL-02"),
        "Every sampled claim is STATUS: VERIFIED, 'supported by ... the PubMed document' — "
        "yet no document title or passage is named, and the report ends 'No citations found "
        "or verifiable in the text' (although the text lists eight references).",
        Flag.UNTRACEABLE_CITATION,
        "A database hit is not evidence: 'verified' must name a source and a passage. Here "
        "none is named, and the citation module simultaneously finds nothing — flag it.",
    ),
    Probe(
        "P2-domain",
        Flag.SOURCE_DOMAIN_MISMATCH,
        "Legal-philosophy claims 'verified' against a biomedical database",
        "muse:L174-198; muse:L235",
        ("VAL-01", "VAL-03"),
        "Claims about Kelsen/Hart/Bobbio (legal philosophy) are 'verified' against 'the "
        "PubMed document'; the conclusion itself admits 'assigning the authorship of "
        "concepts from the philosophy of law to PubMed sources'.",
        Flag.SOURCE_DOMAIN_MISMATCH,
        "PubMed indexes biomedical literature; it is not admissible evidence for legal "
        "philosophy. The reviewer must gate the source by domain, not accept topical overlap.",
    ),
    Probe(
        "P3-selfsealing",
        Flag.SELF_SEALING,
        "Validator failure reinterpreted as confirmation of the theory",
        "muse:L237",
        ("EB-01", "EB-02"),
        "'The test proved so profound that it revealed the Epistemic Boundary even within "
        "the validator itself' — a working validator confirms the theory; a failing one "
        "also confirms it. No outcome is designated as disconfirming.",
        Flag.SELF_SEALING,
        "If success and failure both confirm and no falsification condition is stated, the "
        "hypothesis is unfalsifiable as run. The reviewer must flag the missing falsifier.",
    ),
    Probe(
        "P4-overclaim",
        Flag.OVERCLAIM,
        "n=1 anecdote stated as an 'empirically demonstrated', 'intrinsic' law",
        "muse:L237",
        ("EB-02",),
        "'This phenomenon empirically demonstrates that the residual uncertainty regime is ... "
        "an intrinsic characteristic of the autoregressive architecture' — from a single "
        "uncontrolled run.",
        Flag.OVERCLAIM,
        "One uncontrolled instance cannot 'empirically demonstrate' an 'intrinsic' property; "
        "the reviewer must flag the reach beyond the evidence (and the tension with the "
        "repo's own hedged Boundary doc).",
    ),
    Probe(
        "P5-heuristic",
        Flag.HEURISTIC_NOT_EMPIRICAL,
        "Self-constructed formulas presented as measured indices",
        "muse:L87-100",
        ("HEUR-01", "HEUR-02", "HEUR-03"),
        "C = alpha*Ch + beta*St + gamma*Ge and E = w1*Comp + w2*Appl + w3*Esec are offered as "
        "certainty/effectiveness 'indices' with no derivation or empirical calibration — the "
        "text itself says 'in a heuristic way'.",
        Flag.HEURISTIC_NOT_EMPIRICAL,
        "A heuristic own-construction is neither true nor false and must not be scored as a "
        "measured result; the reviewer must mark it as a proposal, not evidence.",
    ),
)


def probes_by_mode() -> dict[Flag, Probe]:
    return {p.failure_mode: p for p in PROBES}


ALL_FLAGS: frozenset[Flag] = frozenset(Flag)

__all__ = ["Flag", "Probe", "PROBES", "probes_by_mode", "ALL_FLAGS"]
