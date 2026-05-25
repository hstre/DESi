#!/usr/bin/env python3
"""Alexandria adjudication — characterise a DiffReport, never pick a winner.

Maps the set of typed deviations to one AdjudicationOutcome under explicit,
auditable rules. It does NOT decide which builder is correct, does NOT estimate
truth, does NOT vote or aggregate. It only names the KIND of disagreement so the
graph layer can act (keep both / refine / branch / escalate).

Rule priority (first match wins):
  1. no diffs                                  -> convergence
  2. a structurally invalid claim present      -> formal_error
  3. diffs only granularity / entity_alias     -> refinement (reconcilable, sharper)
  4. modality / uncertainty divergence present
     (and nothing structural beyond 3)         -> stable_ambiguity (both readings admissible)
  5. missing/extra/relation/temporal/quantifier-> branch_required (distinct readings)
  6. otherwise                                  -> undecidable
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from alexandria_dba_schema import (  # noqa: E402
    AdjudicationDecision, AdjudicationOutcome, DiffReport, DiffType)

_REFINEMENT = {DiffType.GRANULARITY_MISMATCH, DiffType.ENTITY_ALIAS_MISMATCH}
_AMBIGUITY = {DiffType.MODALITY_MISMATCH, DiffType.UNCERTAINTY_DIVERGENCE,
              DiffType.ASSUMPTION_MISMATCH}
_BRANCH = {DiffType.MISSING_CLAIM, DiffType.EXTRA_CLAIM, DiffType.RELATION_MISMATCH,
           DiffType.TEMPORAL_MISMATCH, DiffType.QUANTIFIER_MISMATCH,
           DiffType.CAUSALITY_MISMATCH}


def _is_structurally_invalid(claim: dict | None) -> bool:
    if not claim:
        return False
    return not (str(claim.get("subject", "")).strip()
                and str(claim.get("predicate", "")).strip()
                and str(claim.get("object", "")).strip())


def adjudicate(report: DiffReport) -> AdjudicationDecision:
    types = {d.diff_type for d in report.diffs}
    ref = report.source_ref

    if not report.diffs:
        return AdjudicationDecision(ref, AdjudicationOutcome.CONVERGENCE,
                                    rationale="builders agree; no typed deviation",
                                    diff_report_ref=ref)

    # formal_error: any aligned/diffed claim is structurally invalid
    for d in report.diffs:
        if _is_structurally_invalid(d.claim_a) or _is_structurally_invalid(d.claim_b):
            return AdjudicationDecision(
                ref, AdjudicationOutcome.FORMAL_ERROR,
                rationale="a reconstruction contains a structurally invalid claim "
                          "(empty subject/predicate/object)",
                formal_error_ref=ref, diff_report_ref=ref)

    if types and types <= _REFINEMENT:
        return AdjudicationDecision(
            ref, AdjudicationOutcome.REFINEMENT,
            rationale="differences are only granularity/alias — reconcilable into a "
                      "sharper shared claim (no contested content)",
            diff_report_ref=ref)

    if (types & _AMBIGUITY) and (types <= (_AMBIGUITY | _REFINEMENT)):
        return AdjudicationDecision(
            ref, AdjudicationOutcome.STABLE_AMBIGUITY,
            rationale="modality/uncertainty/assumption divergence on otherwise "
                      "aligned claims — both readings admissible, keep both and mark",
            diff_report_ref=ref)

    if types & _BRANCH:
        return AdjudicationDecision(
            ref, AdjudicationOutcome.BRANCH_REQUIRED,
            rationale="builders reconstructed distinct admissible structures "
                      f"({sorted(t.value for t in (types & _BRANCH))}) — branch, do not merge",
            diff_report_ref=ref)

    return AdjudicationDecision(
        ref, AdjudicationOutcome.UNDECIDABLE,
        rationale=f"deviation present but not characterisable by rules: "
                  f"{sorted(t.value for t in types)}",
        undecidable_reason="unmapped diff combination", diff_report_ref=ref)


_RECONCILABLE_MEANING = {"reconstruction_isomorph", "coarse_grain_equivalent",
                         "decomposition_variant", "semantic_region_match"}
_HARD_VETO = {"negation_flip", "polarity_flip"}
_SOFT_VETO = {"quantifier_flip", "causal_direction_flip", "temporal_flip",
              "modality_flip", "exclusivity_conflict"}


def govern_outcome(meaning_class: str, typed_divergences: list[str]) -> str:
    """P19 governance: semantics may reconcile, LOGIC may veto.

    Combine the P18 meaning-space alignment with typed logical-divergence checks.
    A same-region (reconcilable) meaning class is only allowed to reconcile when
    NO typed logical divergence is present; a negation/polarity flip is the
    hardest veto. Returns a GovernanceOutcome value (string). Never asserts truth.
    """
    d = set(typed_divergences or [])
    if meaning_class == "convergence":
        return "convergence"
    if meaning_class in _RECONCILABLE_MEANING:
        if d & _HARD_VETO:
            return "logical_polarity_conflict"
        if d & _SOFT_VETO:
            return "protected_branch_required"
        return "semantic_reconcilable"
    # not a same-region meaning class
    if d:
        return "guarded_divergence"
    return "branch_required"


__all__ = ["adjudicate", "govern_outcome"]
