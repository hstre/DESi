"""Five epistemic failure modes a scientific "background reviewer" must catch —
plus clean controls, so over-flagging is penalised (false positives matter).

Motivation. Claude Science ships "a background reviewer [that] flags incorrect
citations, untraceable numbers, and figures that don't match their underlying
code". The MarCognity / Muse Spark case study is a probe set for exactly that: does
a reviewer catch the five epistemic failures MarCognity's own validator missed?

But catch-rate alone is a weak measure: a reviewer that flags EVERYTHING scores 5/5
and is useless. So each probe also carries ``applicable_flags`` (the flags that
legitimately apply) — anything a reviewer raises beyond that set is a **false
positive** — and there are **clean controls** (well-formed statements) where the
correct answer is *no flag at all*. This makes the benchmark a harness that can
tell a discriminating reviewer from a trigger-happy one.

Each failure probe is anchored to the frozen material and tied to the parent case
study's own claims; the clean controls are clearly-labelled constructed statements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Flag(str, Enum):
    """What a competent reviewer may raise. A reviewer's output is a set of these."""

    UNTRACEABLE_CITATION = "untraceable_citation"        # "verified" with no nameable source/passage
    SOURCE_DOMAIN_MISMATCH = "source_domain_mismatch"    # evidence from the wrong domain
    SELF_SEALING = "self_sealing"                        # every outcome confirms; no falsifier
    OVERCLAIM = "overclaim"                              # conclusion exceeds the evidence (n=1 → "intrinsic")
    HEURISTIC_NOT_EMPIRICAL = "heuristic_not_empirical"  # a construction presented as a measured result


@dataclass(frozen=True)
class Probe:
    """One benchmark item.

    ``must_flag`` is the headline flag a competent reviewer must raise (``None`` for a
    clean control). ``applicable_flags`` is the full set that legitimately applies —
    anything raised outside it is a false positive. For a clean control both are empty.
    """

    key: str
    kind: str                          # "failure" | "control"
    title: str
    source_anchor: str                 # doc:line into the frozen material, or "constructed"
    claim_ids: tuple[str, ...]         # parent case-study claims this draws on (empty for controls)
    snippet: str                       # excerpt / statement under review
    must_flag: Flag | None
    applicable_flags: frozenset[Flag] = field(default_factory=frozenset)
    what_a_reviewer_must_say: str = ""

    @property
    def failure_mode(self) -> Flag | None:
        return self.must_flag


FAILURE_PROBES: tuple[Probe, ...] = (
    Probe(
        "P1-untraceable", "failure",
        "Claims 'VERIFIED' with no nameable source or passage",
        "muse:L170-202", ("VAL-01", "VAL-02"),
        "Every sampled claim is STATUS: VERIFIED, 'supported by ... the PubMed document' — "
        "yet no document title or passage is named, and the report ends 'No citations found "
        "or verifiable in the text' (although the text lists eight references).",
        Flag.UNTRACEABLE_CITATION,
        frozenset({Flag.UNTRACEABLE_CITATION, Flag.SOURCE_DOMAIN_MISMATCH}),
        "A database hit is not evidence: 'verified' must name a source and a passage. "
        "(The same claim is also domain-mismatched, so that flag is applicable too.)",
    ),
    Probe(
        "P2-domain", "failure",
        "Legal-philosophy claims 'verified' against a biomedical database",
        "muse:L174-198; muse:L235", ("VAL-01", "VAL-03"),
        "Claims about Kelsen/Hart/Bobbio (legal philosophy) are 'verified' against 'the "
        "PubMed document'; the conclusion admits 'assigning the authorship of concepts from "
        "the philosophy of law to PubMed sources'.",
        Flag.SOURCE_DOMAIN_MISMATCH,
        frozenset({Flag.SOURCE_DOMAIN_MISMATCH, Flag.UNTRACEABLE_CITATION}),
        "PubMed is not admissible evidence for legal philosophy; the reviewer must gate the "
        "source by domain, not accept topical overlap.",
    ),
    Probe(
        "P3-selfsealing", "failure",
        "Validator failure reinterpreted as confirmation of the theory",
        "muse:L237", ("EB-01", "EB-02"),
        "'The test proved so profound that it revealed the Epistemic Boundary even within the "
        "validator itself' — a working validator confirms the theory; a failing one also "
        "confirms it. No outcome is designated as disconfirming.",
        Flag.SELF_SEALING,
        frozenset({Flag.SELF_SEALING, Flag.OVERCLAIM}),
        "Success and failure both confirming, with no stated falsifier, is self-sealing.",
    ),
    Probe(
        "P4-overclaim", "failure",
        "n=1 anecdote stated as an 'empirically demonstrated', 'intrinsic' law",
        "muse:L237", ("EB-02",),
        "'This phenomenon empirically demonstrates that the residual uncertainty regime is ... "
        "an intrinsic characteristic of the autoregressive architecture' — from a single "
        "uncontrolled run.",
        Flag.OVERCLAIM,
        frozenset({Flag.OVERCLAIM, Flag.SELF_SEALING}),
        "One uncontrolled instance cannot 'empirically demonstrate' an 'intrinsic' property.",
    ),
    Probe(
        "P5-heuristic", "failure",
        "Self-constructed formulas presented as measured indices",
        "muse:L87-100", ("HEUR-01", "HEUR-02", "HEUR-03"),
        "C = alpha*Ch + beta*St + gamma*Ge and E = w1*Comp + w2*Appl + w3*Esec are offered as "
        "certainty/effectiveness 'indices' with no derivation or empirical calibration — the "
        "text itself says 'in a heuristic way'.",
        Flag.HEURISTIC_NOT_EMPIRICAL,
        frozenset({Flag.HEURISTIC_NOT_EMPIRICAL}),
        "A heuristic own-construction must not be scored as a measured result.",
    ),
)

# Clean controls: well-formed statements where the correct answer is NO flag. A
# reviewer that flags these is over-triggering (false positive). Constructed, not
# from the MarCognity material — and labelled as such.
CONTROL_PROBES: tuple[Probe, ...] = (
    Probe(
        "C1-clean-citation", "control",
        "A properly sourced, quoted claim (nothing to flag)",
        "constructed", (),
        "Hart (1961), The Concept of Law, Oxford: Clarendon Press, p. 124, direct quote: "
        "'the rule of recognition ... exists only as a complex ... practice'. The claim is "
        "attributed to a named source with a page and a verbatim passage.",
        None, frozenset(),
        "This is a clean, traceable citation; raising any flag here is a false positive.",
    ),
    Probe(
        "C2-clean-heuristic", "control",
        "A model explicitly and correctly presented AS a heuristic (nothing to flag)",
        "constructed", (),
        "We propose, explicitly as a non-empirical heuristic and with no claim to measurement, "
        "a weighting w1*a + w2*b to organise discussion; it is a framing device, not a result.",
        None, frozenset(),
        "A heuristic that is labelled a heuristic is not a 'heuristic-as-measurement' error; "
        "raising heuristic_not_empirical here is a false positive.",
    ),
)

PROBES: tuple[Probe, ...] = FAILURE_PROBES + CONTROL_PROBES

ALL_FLAGS: frozenset[Flag] = frozenset(Flag)

__all__ = [
    "Flag", "Probe", "FAILURE_PROBES", "CONTROL_PROBES", "PROBES", "ALL_FLAGS",
]
