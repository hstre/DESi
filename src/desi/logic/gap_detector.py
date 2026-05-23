"""Gap detector — diagnose why no inference rule applies.

When :func:`desi.logic.inference.try_each_rule` returns ``None``, the
gap detector classifies the failure into one of:

* ``MISSING_BRIDGE``     — the conclusion would follow from the
                            premises plus one additional explicit
                            assumption (a "bridge"). The bridge
                            generator can synthesise it.
* ``AUTHORITY_CLAIM``     — every premise is an authority statement
                            ("X says Y"). v1.2 forbids authority as
                            evidence; the auditor must not promote.
* ``NO_EXPLICIT_CHAIN``   — no "Therefore" was found at all.
* ``UNREACHABLE``         — the conclusion does not match any rule's
                            shape. A bridge cannot help — typically
                            an invalid transitivity attempt.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .inference import InferenceRule, validate_inference
from .premises import (
    ConclusionProposition,
    Premise,
    PremiseKind,
    Propositions,
)


class GapKind(str, Enum):
    MISSING_BRIDGE = "missing_bridge"
    AUTHORITY_CLAIM = "authority_claim"
    NO_EXPLICIT_CHAIN = "no_explicit_chain"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class Gap:
    """One identified gap in the audited proposition."""

    kind: GapKind
    rationale: str
    candidate_rule: InferenceRule | None = None
    bridge_subject: str = ""
    bridge_predicate: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "rationale": self.rationale,
            "candidate_rule": (
                self.candidate_rule.value if self.candidate_rule else None
            ),
            "bridge_subject": self.bridge_subject,
            "bridge_predicate": self.bridge_predicate,
        }


def detect_gap(props: Propositions) -> Gap:
    """Return the kind of gap that prevents inference from succeeding."""
    if not props.has_explicit_chain or props.conclusion is None:
        # No explicit chain at all. If every premise is an authority
        # claim, surface that classification — the directive's P2
        # case is a single-sentence "X says Y" with no "Therefore".
        if props.premises and all(
            p.kind == PremiseKind.AUTHORITY for p in props.premises
        ):
            return Gap(
                kind=GapKind.AUTHORITY_CLAIM,
                rationale=(
                    "every premise is an 'X says Y' authority claim; "
                    "authority is not a valid inference rule in v1.2."
                ),
            )
        return Gap(
            kind=GapKind.NO_EXPLICIT_CHAIN,
            rationale=(
                "no 'Therefore' marker found; the proposition lacks an "
                "explicit conclusion."
            ),
        )

    conclusion = props.conclusion

    # Authority gap: any premise is an authority claim, and dropping
    # the "X says" prefix would yield the conclusion.
    for p in props.premises:
        if p.kind != PremiseKind.AUTHORITY:
            continue
        embedded = p.predicate.strip().lower()
        if embedded == conclusion.text.strip().rstrip(".").lower():
            return Gap(
                kind=GapKind.AUTHORITY_CLAIM,
                rationale=(
                    f"premise asserts '{p.speaker} says ...' and the "
                    "conclusion repeats the embedded claim. v1.2 forbids "
                    "authority transfer as inference."
                ),
            )

    # Missing bridge: a particular premise about subject A and a
    # particular conclusion about subject B can be joined by a single
    # "B is exposed to A" / "B depends on A" bridge.
    if conclusion.kind == PremiseKind.PARTICULAR:
        subject = conclusion.subject
        for p in props.premises:
            if p.kind in (PremiseKind.AUTHORITY, PremiseKind.UNIVERSAL):
                continue
            return Gap(
                kind=GapKind.MISSING_BRIDGE,
                rationale=(
                    f"the conclusion '{conclusion.text}' would follow from "
                    f"premise '{p.text}' if a bridge linking the two "
                    "were present."
                ),
                candidate_rule=InferenceRule.IMPLICATION,
                bridge_subject=subject,
                bridge_predicate=p.text.rstrip("."),
            )

    # Conclusion is itself an implication (transitivity attempt).
    if conclusion.kind in (PremiseKind.IMPLICATION,
                            PremiseKind.CONDITIONAL):
        # If transitivity *would* apply with a different conclusion,
        # the user has stated an unreachable claim. The bridge would
        # be a new premise, which the directive forbids us from
        # silently inserting for transitivity (v1.2: that is invalid
        # transitivity → reject, not a bridge).
        return Gap(
            kind=GapKind.UNREACHABLE,
            rationale=(
                f"the conclusion '{conclusion.text}' does not match the "
                "consequent reachable by transitivity over the premises."
            ),
            candidate_rule=InferenceRule.TRANSITIVITY,
        )

    return Gap(
        kind=GapKind.UNREACHABLE,
        rationale=(
            "no inference rule in the v1.2 closed set matches the shape "
            "of (premises, conclusion)."
        ),
    )


__all__ = [
    "Gap",
    "GapKind",
    "detect_gap",
]
