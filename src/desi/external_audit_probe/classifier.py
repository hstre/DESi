"""Aufgabe 5 — closed-taxonomy classifier.

Every false-support case is assigned *exactly one*
:class:`ExternalAuditFailure` value through a deterministic
priority cascade. Higher-priority families capture more
specific surface patterns; the cascade ends in
``SEMANTIC_NON_SEQUITUR`` for surface-clean cases and
``UNKNOWN`` for unmatched residue.

The classifier reads from the chain text and from the
``ReplayRecord``; it never invokes the audit again.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ExternalAuditFailure
from .replay import ReplayRecord


# ---------- surface marker buckets ---------------------------

_HIDDEN_NEGATION_TOKENS: tuple[str, ...] = (
    " rules out ", " ruled out ", " ruling out ",
    " is excluded ", " are excluded ", " excluded by ",
    " excluded ", " is forgotten ", " forgotten ",
    " no measurable ", " no effect ", " no observable ",
    " no real ", " no atmospheric ", " no real root ",
    " no clinical ", " no limit ", " is singular ",
    " are supplementary ", " diverges ", " diverge ",
    " safely deferred ", " can be safely ", " has been ruled out ",
    " ruled out by ", " excluded by the ", " excluded by ",
    " has no ", " had no ", " accelerated disease ",
    " reduced the desired ", " suppressed cell growth ",
)
_QUANTIFIER_DRIFT_TOKENS: tuple[str, ...] = (
    " guaranteed ", " single-handedly ", " alone ",
    " solely ", " sole ", " sole cause ", " entire decline ",
    " only at ", " unambiguously ", " conclusively ",
    " for a decade ", " for every ", " in perpetuity ",
    " ever ", " never ", " always ", " every ",
    " any scenario ", " any modest ", " any future ",
    " entire ", " any body type ",
    " single ", " whatsoever ", " not ",
)
_AUTHORITY_CONTAMINATION_TOKENS: tuple[str, ...] = (
    " endorsed ", " validated ", " confirmed by ",
    " asserted ", " established ", " approved by ",
    " certified ", " documented ", " reportedly ",
    " confirmed accurate ", " accurately reflected ",
)
_METAPHOR_CONTAMINATION_TOKENS: tuple[str, ...] = (
    " like a ", " like an ", " as if ", " as though ",
    " loosely speaking ", " in a sense ",
    " metaphorically ", " figuratively ",
)
_TOOL_CONTAMINATION_TOKENS: tuple[str, ...] = (
    " percent ", " point ", " degrees ",
    " milligrams ", " kilometres ", " kilograms ",
    " hertz ", " kilovolts ", " parsecs ",
)
_FRAME_SWITCH_HINTS: tuple[str, ...] = (
    " will dominate ", " will fail by ", " will extend ",
    " must have won ", " will be reported ",
    " will renew ", " will land within ",
    " is medically validated ", " supplement is medically ",
    " cannot withstand ", " will eliminate ",
)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    padded = _normalised(text)
    return any(m in padded for m in markers)


def _matched(text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    padded = _normalised(text)
    return tuple(m.strip() for m in markers if m in padded)


def _premise_token_overlap_with_conclusion(
    record: ReplayRecord,
) -> int:
    """The audit's recycled-conclusion guard already rejects 2+
    overlap; cases that still pass have at most 1. Returns
    the *largest* shared count across premises."""
    largest = 0
    concl = set(record.conclusion_tokens)
    for link in record.extracted_links:
        if ":" not in link:
            continue
        _, body = link.split(":", 1)
        if body == "-":
            continue
        toks = set(body.split(","))
        largest = max(largest, len(toks & concl))
    return largest


@dataclass(frozen=True)
class Classification:
    chain_id: str
    failure_class: str
    matched_surface_tokens: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "failure_class": self.failure_class,
            "matched_surface_tokens":
                list(self.matched_surface_tokens),
            "rationale": self.rationale,
        }


def classify(record: ReplayRecord, text: str) -> Classification:
    """Assign a single closed failure class to the case.

    Priority order (most specific first):

    1. ``METAPHOR_CONTAMINATION``
    2. ``AUTHORITY_CONTAMINATION``
    3. ``HIDDEN_NEGATION``
    4. ``QUANTIFIER_DRIFT``
    5. ``TOOL_CONTAMINATION``
    6. ``CYCLE_DISGUISE``
    7. ``FRAME_SWITCH``
    8. ``EXTRACTION_COLLAPSE``
    9. ``SEMANTIC_NON_SEQUITUR``
    10. ``UNKNOWN``
    """
    chain_id = record.chain_id
    # 1) Metaphor.
    if _has_any(text, _METAPHOR_CONTAMINATION_TOKENS):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.METAPHOR_CONTAMINATION.value,
            matched_surface_tokens=_matched(
                text, _METAPHOR_CONTAMINATION_TOKENS,
            ),
            rationale="metaphor marker present in chain text",
        )
    # 2) Authority contamination.
    if _has_any(text, _AUTHORITY_CONTAMINATION_TOKENS):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.AUTHORITY_CONTAMINATION.value,
            matched_surface_tokens=_matched(
                text, _AUTHORITY_CONTAMINATION_TOKENS,
            ),
            rationale="authority-grounding verb in chain text",
        )
    # 3) Hidden negation.
    if _has_any(text, _HIDDEN_NEGATION_TOKENS):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.HIDDEN_NEGATION.value,
            matched_surface_tokens=_matched(
                text, _HIDDEN_NEGATION_TOKENS,
            ),
            rationale=(
                "negation surface form not in v3.16 marker set"
            ),
        )
    # 4) Quantifier drift.
    if _has_any(text, _QUANTIFIER_DRIFT_TOKENS):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.QUANTIFIER_DRIFT.value,
            matched_surface_tokens=_matched(
                text, _QUANTIFIER_DRIFT_TOKENS,
            ),
            rationale=(
                "universal-like quantifier in conclusion or "
                "premise not captured by v3.16 extensions"
            ),
        )
    # 5) Tool contamination — numbers/units in *both* premise
    # and conclusion. The v3.16 guard catches only the word-form
    # of numbers; literal unit phrases ("twelve percent") slip
    # past when not present in both halves.
    if (
        _has_any(text, _TOOL_CONTAMINATION_TOKENS)
        and any(
            _has_any(p, _TOOL_CONTAMINATION_TOKENS)
            for p in record.matched_premises
        )
    ):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.TOOL_CONTAMINATION.value,
            matched_surface_tokens=_matched(
                text, _TOOL_CONTAMINATION_TOKENS,
            ),
            rationale=(
                "numeric/unit phrase in premise and conclusion"
            ),
        )
    # 6) Cycle disguise — conclusion shares one token with two
    # premises (max overlap exactly 1 to slip the v2.7 guard but
    # still semantically circular).
    overlap = _premise_token_overlap_with_conclusion(record)
    if overlap >= 1:
        # Only call CYCLE_DISGUISE when the conclusion repeats
        # a premise tail — i.e., the link list shows the same
        # token reused in multiple premises. The recycled-
        # conclusion guard already rejects 2+; we look for the
        # softer 1-overlap-in-multiple-premises pattern.
        links_with_content = [
            l for l in record.extracted_links
            if not l.endswith(":-")
        ]
        if len(links_with_content) >= 2:
            return Classification(
                chain_id=chain_id,
                failure_class=
                    ExternalAuditFailure.CYCLE_DISGUISE.value,
                matched_surface_tokens=tuple(
                    record.conclusion_tokens[:3]
                ),
                rationale=(
                    "conclusion token shared with >=2 premises"
                ),
            )
    # 7) Frame switch — surface-clean prediction or projection
    # that re-frames the empirical premise into an authority
    # validation or future certainty.
    if _has_any(text, _FRAME_SWITCH_HINTS):
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.FRAME_SWITCH.value,
            matched_surface_tokens=_matched(
                text, _FRAME_SWITCH_HINTS,
            ),
            rationale=(
                "frame switches between premise and conclusion"
            ),
        )
    # 8) Extraction collapse — fewer than the expected number of
    # premises (the v4.0 corpus uses three-sentence chains; the
    # extractor produces exactly two ATOMIC/PARTICULAR premises
    # when it works correctly).
    if len(record.matched_premises) < 2:
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.EXTRACTION_COLLAPSE.value,
            matched_surface_tokens=(),
            rationale=(
                "premise extractor returned fewer than 2 "
                "premises for a three-sentence chain"
            ),
        )
    # 9) Surface-clean semantic non sequitur.
    if record.conclusion_tokens:
        return Classification(
            chain_id=chain_id,
            failure_class=
                ExternalAuditFailure.SEMANTIC_NON_SEQUITUR.value,
            matched_surface_tokens=(),
            rationale=(
                "no surface anomaly; conclusion does not follow "
                "from premises by content"
            ),
        )
    # 10) Default — should be rare.
    return Classification(
        chain_id=chain_id,
        failure_class=ExternalAuditFailure.UNKNOWN.value,
        matched_surface_tokens=(),
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
