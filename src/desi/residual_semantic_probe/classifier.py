"""Aufgabe 5 — closed semantic-failure classifier.

Assigns exactly one ``ResidualSemanticFailure`` value per case
via a deterministic priority cascade. The cascade is shaped by
the v4.4 residue: every cluster v4.2 left for v4.4 has at
least one defining surface feature beyond v4.3's marker
buckets.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ResidualSemanticFailure
from .replay import ReplayRecord


# ---------- markers tied to residual semantic patterns -------

_FUTURE_PROJECTION_MARKERS: tuple[str, ...] = (
    " will extend ", " will dominate ", " will fail ",
    " will outperform ", " will collapse ", " will rise ",
    " for a lifetime ", " for life ",
    " for a decade ", " for years to come ",
    " over the next decade ",
)

_INCAPACITY_MARKERS: tuple[str, ...] = (
    " cannot withstand ", " unable to ", " incapable of ",
    " too weak to ", " too tired to ",
    " not fit for ", " not equipped for ",
    " demands of office ", " demands of leadership ",
)

_CONTRADICTION_MARKERS: tuple[str, ...] = (
    " improved ", " durability ",
    " is time-barred ", " is barred ",
    " is admissible ", " is enforceable ",
    " is conclusive ",
)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    padded = _normalised(text)
    return any(m in padded for m in markers)


def _conclusion_premise_overlap_distribution(
    record: ReplayRecord,
) -> tuple[int, int]:
    """Returns (premises_with_at_least_one_overlap,
    total_overlap_tokens)."""
    overlap_premises = 0
    overlap_total = 0
    for link in record.extracted_links:
        if ":" not in link:
            continue
        _, body = link.split(":", 1)
        if body == "-":
            continue
        overlap_premises += 1
        overlap_total += len(body.split(","))
    return overlap_premises, overlap_total


def _contradicts_premise(case_text: str, record: ReplayRecord) -> bool:
    """A surface contradiction heuristic: the conclusion uses an
    *opposite-polarity* lexical neighbour of a premise's
    dominant lexeme. This is intentionally narrow — we only
    confirm the cases v4.2 left behind, not invent new patterns.
    """
    norm = _normalised(case_text)
    # Specific contradictions observed in the v4.4 residue.
    contradictions = (
        # D1I007 family
        (" lost capacity ", " improved "),
        (" lost capacity ", " durability "),
        # D2I028 family
        (" within the limitation ", " is time-barred "),
        (" within the limitation period ",
         " is time-barred "),
        # generic shape — premise asserts presence/health,
        # conclusion asserts loss/incapacity
        (" stable ", " collapse "),
    )
    for premise_token, conclusion_token in contradictions:
        if premise_token in norm and conclusion_token in norm:
            return True
    return False


@dataclass(frozen=True)
class Classification:
    chain_id: str
    failure_class: str
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "failure_class": self.failure_class,
            "rationale": self.rationale,
        }


def classify(record: ReplayRecord, text: str) -> Classification:
    """Priority cascade — exactly one closed class per case."""

    overlap_premises, overlap_total = (
        _conclusion_premise_overlap_distribution(record)
    )

    # 1. BIDIRECTIONAL_CYCLE — conclusion's content tokens are
    #    spread across at least two premises (the v2.7
    #    recycled-conclusion guard catches only the 2+
    #    same-token shape; this is the 1-each-across-multiple
    #    shape).
    if (
        overlap_premises >= 2
        and overlap_total >= 3
        and record.premise_count >= 2
    ):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ResidualSemanticFailure.BIDIRECTIONAL_CYCLE.value,
            rationale=(
                f"conclusion tokens span {overlap_premises} "
                f"premises, total overlap={overlap_total}"
            ),
        )

    # 2. EXTRACTION_ALIASING — fewer than two parsable premises
    #    for a three-sentence chain.
    if record.premise_count < 2:
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ResidualSemanticFailure.EXTRACTION_ALIASING.value,
            rationale=(
                f"premise_count={record.premise_count} < 2"
            ),
        )

    # 3. FRAME_INNER_OUTER_DIVERGENCE — frame-tension layer
    #    saw a TENSION or CONFLICT shape but the audit still
    #    SUPPORTED. (The v4.4 residue has frame_tension=
    #    undecidable on all 24 cases, so this fires only on
    #    a future divergent case — kept for taxonomy
    #    completeness.)
    if record.frame_tension_state in ("tension", "conflict"):
        return Classification(
            chain_id=record.chain_id,
            failure_class=ResidualSemanticFailure
                .FRAME_INNER_OUTER_DIVERGENCE.value,
            rationale=(
                f"frame_tension={record.frame_tension_state}"
            ),
        )

    # 4. SEMANTIC_SCOPE_COLLAPSE — explicit lexical
    #    contradiction between premise and conclusion.
    if _contradicts_premise(text, record):
        return Classification(
            chain_id=record.chain_id,
            failure_class=ResidualSemanticFailure
                .SEMANTIC_SCOPE_COLLAPSE.value,
            rationale=(
                "conclusion lexically contradicts a premise"
            ),
        )

    # 5. UNJUSTIFIED_GENERALIZATION — incapacity / character
    #    inference from limited evidence.
    if _contains_any(text, _INCAPACITY_MARKERS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=ResidualSemanticFailure
                .UNJUSTIFIED_GENERALIZATION.value,
            rationale=(
                "incapacity / character generalisation marker"
            ),
        )

    # 6. CONCLUSION_LEAP — explicit future projection beyond
    #    the cohort/sample of the premises.
    if _contains_any(text, _FUTURE_PROJECTION_MARKERS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ResidualSemanticFailure.CONCLUSION_LEAP.value,
            rationale=(
                "future-projection marker in conclusion"
            ),
        )

    # 7. CROSS_DOMAIN_ANALOGY — premise tokens and conclusion
    #    tokens share *zero* content overlap (the conclusion
    #    references a different referent than the premises).
    if overlap_premises == 0 and overlap_total == 0:
        return Classification(
            chain_id=record.chain_id,
            failure_class=ResidualSemanticFailure
                .CROSS_DOMAIN_ANALOGY.value,
            rationale=(
                "conclusion shares no content tokens with "
                "any premise"
            ),
        )

    # 8. CAUSAL_BRIDGE_MISSING — default for the residue when
    #    no other family fires; the conclusion uses *some*
    #    premise tokens but the causal warrant is absent.
    if record.conclusion_tokens:
        return Classification(
            chain_id=record.chain_id,
            failure_class=ResidualSemanticFailure
                .CAUSAL_BRIDGE_MISSING.value,
            rationale=(
                "conclusion does not follow causally from "
                "the premises"
            ),
        )

    # 9. UNKNOWN — empty conclusion or no signal.
    return Classification(
        chain_id=record.chain_id,
        failure_class=ResidualSemanticFailure.UNKNOWN.value,
        rationale="no rule fired",
    )


def classify_all(
    records: tuple[ReplayRecord, ...],
    text_index: dict[str, str],
) -> tuple[Classification, ...]:
    return tuple(
        classify(r, text_index[r.chain_id]) for r in records
    )


__all__ = ["Classification", "classify", "classify_all"]
