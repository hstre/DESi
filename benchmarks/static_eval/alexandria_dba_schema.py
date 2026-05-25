#!/usr/bin/env python3
"""Alexandria Dual-Builder Adjudication (DBA) — prototype SCHEMA only.

Data structures for the selective cross-assessment layer. There is **no API, no
model call, and no diff/adjudication logic here** — this file defines the shapes a
future cross-assessment would produce and consume. It is Alexandria-conformant by
construction: it models *parallel independent reconstructions* and the *deviation*
between them, NOT a jury, a vote, an aggregation, or a truth estimate.

Pipeline these shapes describe (not implemented here):
    unit -> N independent BuilderOutput (different builders/models)
         -> N BuilderGraph (each builder's structured reconstruction)
         -> pairwise DiffReport (deviation detection, typed)
         -> AdjudicationDecision (characterise the deviation; never "pick a winner")
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class DiffType(str, Enum):
    """Typed deviation between two independent reconstructions of the same unit."""
    MISSING_CLAIM = "missing_claim"
    EXTRA_CLAIM = "extra_claim"
    GRANULARITY_MISMATCH = "granularity_mismatch"
    MODALITY_MISMATCH = "modality_mismatch"
    QUANTIFIER_MISMATCH = "quantifier_mismatch"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    RELATION_MISMATCH = "relation_mismatch"
    CAUSALITY_MISMATCH = "causality_mismatch"
    EVIDENCE_MISMATCH = "evidence_mismatch"
    UNCERTAINTY_DIVERGENCE = "uncertainty_divergence"
    ASSUMPTION_MISMATCH = "assumption_mismatch"
    CATEGORY_MISMATCH = "category_mismatch"
    ENTITY_ALIAS_MISMATCH = "entity_alias_mismatch"


class AdjudicationOutcome(str, Enum):
    """How a deviation is characterised — explicitly NOT a winner/vote.

    convergence      builders agree (no material deviation) -> no action
    refinement       deviation resolved into a more precise shared claim
    stable_ambiguity genuine, irreducible ambiguity -> keep both, mark ambiguous
    formal_error     one reconstruction is structurally/logically invalid
    branch_required  deviation reflects distinct admissible readings -> branch
    undecidable      cannot be characterised from available evidence -> escalate/log
    """
    CONVERGENCE = "convergence"
    REFINEMENT = "refinement"
    STABLE_AMBIGUITY = "stable_ambiguity"
    FORMAL_ERROR = "formal_error"
    BRANCH_REQUIRED = "branch_required"
    UNDECIDABLE = "undecidable"


@dataclass
class BuilderOutput:
    """Raw output of ONE independent builder for one source unit."""
    builder_id: str                       # e.g. "granite", "deepseek"
    model: str                            # concrete model id
    source_ref: str                       # unit / task identifier
    raw_text: str = ""                    # the builder's raw response
    claims: list[dict] = field(default_factory=list)  # extracted atomic claims
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BuilderGraph:
    """Structured reconstruction (claim graph) from ONE builder."""
    builder_id: str
    model: str
    source_ref: str
    nodes: list[dict] = field(default_factory=list)   # canonical claims
    edges: list[dict] = field(default_factory=list)   # relations
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiffItem:
    """One typed deviation between builder_a's and builder_b's reconstruction."""
    diff_type: DiffType
    builder_a: str
    builder_b: str
    claim_a: Optional[dict] = None        # the claim in A (or None if missing)
    claim_b: Optional[dict] = None        # the claim in B (or None if missing)
    detail: str = ""
    severity: str = "info"                # info | minor | major (descriptive only)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["diff_type"] = self.diff_type.value
        return d


@dataclass
class DiffReport:
    """All typed deviations found between two builder graphs for one unit."""
    source_ref: str
    builder_a: str
    builder_b: str
    diffs: list[DiffItem] = field(default_factory=list)
    created_at: str = ""

    def counts_by_type(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.diffs:
            out[d.diff_type.value] = out.get(d.diff_type.value, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"source_ref": self.source_ref, "builder_a": self.builder_a,
                "builder_b": self.builder_b, "created_at": self.created_at,
                "diffs": [d.to_dict() for d in self.diffs],
                "counts_by_type": self.counts_by_type()}


@dataclass
class AdjudicationDecision:
    """Characterisation of a DiffReport. Never picks a 'true' answer."""
    source_ref: str
    outcome: AdjudicationOutcome
    rationale: str = ""
    refined_claim: Optional[dict] = None          # set only for REFINEMENT
    branch_ids: list[str] = field(default_factory=list)  # set only for BRANCH_REQUIRED
    formal_error_ref: Optional[str] = None        # set only for FORMAL_ERROR
    undecidable_reason: str = ""                   # set only for UNDECIDABLE
    diff_report_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d


def json_schema() -> dict[str, Any]:
    """Lightweight, dependency-free schema description (field -> type) for docs."""
    return {
        "DiffType": [t.value for t in DiffType],
        "AdjudicationOutcome": [o.value for o in AdjudicationOutcome],
        "BuilderOutput": {"builder_id": "str", "model": "str", "source_ref": "str",
                          "raw_text": "str", "claims": "list[dict]",
                          "created_at": "str", "notes": "str"},
        "BuilderGraph": {"builder_id": "str", "model": "str", "source_ref": "str",
                         "nodes": "list[dict]", "edges": "list[dict]",
                         "provenance": "dict"},
        "DiffItem": {"diff_type": "DiffType", "builder_a": "str", "builder_b": "str",
                     "claim_a": "dict|None", "claim_b": "dict|None",
                     "detail": "str", "severity": "info|minor|major"},
        "DiffReport": {"source_ref": "str", "builder_a": "str", "builder_b": "str",
                       "diffs": "list[DiffItem]", "created_at": "str"},
        "AdjudicationDecision": {"source_ref": "str", "outcome": "AdjudicationOutcome",
                                 "rationale": "str", "refined_claim": "dict|None",
                                 "branch_ids": "list[str]",
                                 "formal_error_ref": "str|None",
                                 "undecidable_reason": "str", "diff_report_ref": "str"},
    }


__all__ = ["AdjudicationDecision", "AdjudicationOutcome", "BuilderGraph",
           "BuilderOutput", "DiffItem", "DiffReport", "DiffType", "json_schema"]


if __name__ == "__main__":
    print(json.dumps(json_schema(), indent=2))
