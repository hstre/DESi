"""Semantic UNFOLDING detector (PERIPHERAL, benchmark adapter).

Most semantic layers use similarity to MERGE/FOLD near-duplicate items. This does
the opposite: it uses deterministic signals to detect *superficially similar but
epistemically dangerous differences* -- the cases where high surface similarity
would tempt a solver to falsely COLLAPSE a claim onto its evidence (false fold).

Core principle: semantic similarity is NOT enough. The system must catch
directional / operator / relation / negation divergence before allowing a
'direct entailment' fold.

Given (claim, evidence) it computes -- deterministically, no LLM, no gold label,
no dataset name -- divergence signals and assigns an unfold-risk category:

    fold_safe                 -- high overlap, no divergence: safe to fold
    contradiction_masking     -- surface-similar but a contradiction is hidden
    directional_divergence    -- relation reversed (X>Y vs Y>X)
    operator_divergence       -- quantifier mismatch (all vs some)
    semantic_near_epistemic_far -- same topic (entities) but different relation
    partial_support_masking   -- claim asserts more than the evidence covers

It reuses the algorithmic micro-router's feature extractor (sibling peripheral
module); it does NOT import or touch the DESi core. Deterministic / replay-stable.
"""
from __future__ import annotations

from dataclasses import dataclass

from micro_semantic_router import MicroSemanticRouter, _entities, _raw_tokens

CATEGORIES = (
    "fold_safe", "contradiction_masking", "directional_divergence",
    "operator_divergence", "semantic_near_epistemic_far", "partial_support_masking",
)

_FOLD_COV = 0.85          # coverage at/above which a fold is considered safe
_NEAR_COV = 0.5           # below this, with shared entities, topic-same/relation-different
_COMPARATIVES = frozenset((
    "larger", "bigger", "greater", "smaller", "less", "fewer", "more", "taller",
    "shorter", "older", "younger", "longer", "higher", "lower", "faster",
    "slower", "exceeds", "exceeded", "outnumber", "outnumbers", "before",
    "after", "precedes", "preceded", "follows", "followed", "predates", "beat",
    "beats", "defeated", "defeats", "above", "below", "north", "south", "east", "west",
))
_UNIVERSAL = frozenset((
    "all", "every", "each", "always", "entire", "whole", "any", "everyone",
    "everything", "everywhere", "both",
))
_EXISTENTIAL = frozenset((
    "some", "most", "many", "few", "several", "sometimes", "often", "certain",
    "partially", "occasionally", "occasional", "minority", "majority",
))


def _has_any(text: str, markers: frozenset) -> bool:
    return any(t.lower() in markers for t in _raw_tokens(text))


def _comparative_pair(text: str, shared: set[str]) -> tuple[str, str] | None:
    """Return (subject, object) = the shared entities flanking the comparative."""
    toks = [t.lower().strip(".") for t in _raw_tokens(text)]
    ci = next((i for i, t in enumerate(toks) if t in _COMPARATIVES), None)
    if ci is None:
        return None
    before = [t for t in toks[:ci] if t in shared]
    after = [t for t in toks[ci + 1:] if t in shared]
    if not before or not after:
        return None
    return (before[-1], after[0])


def _directional_reversal(claim: str, evidence: str, shared: set[str]) -> bool:
    if len(shared) < 2:
        return False
    pc = _comparative_pair(claim, shared)
    pe = _comparative_pair(evidence, shared)
    if not pc or not pe:
        return False
    # same comparative relation, but subject/object swapped -> reversed direction
    return pc[0] == pe[1] and pc[1] == pe[0] and pc[0] != pc[1]


def _operator_divergence(claim: str, evidence: str) -> bool:
    cu, eu = _has_any(claim, _UNIVERSAL), _has_any(evidence, _UNIVERSAL)
    ce, ee = _has_any(claim, _EXISTENTIAL), _has_any(evidence, _EXISTENTIAL)
    return (cu and ee) or (ce and eu)


@dataclass(frozen=True)
class UnfoldResult:
    category: str       # one of CATEGORIES
    unfold: bool        # True if an epistemically-dangerous divergence is present
    applicable: bool    # True if this is a fold candidate (enough surface similarity)
    signals: dict
    reason: str


class SemanticUnfoldingDetector:
    """Deterministic unfolding detector. No LLM, no gold label, no dataset name."""

    def __init__(self) -> None:
        self._micro = MicroSemanticRouter()

    def detect(self, claim: str, evidence: str) -> UnfoldResult:
        f = self._micro.features(claim, evidence)
        cov = f["content_coverage_claim"]
        ent = f["entity_overlap"]
        shared_n = f["shared_entities"]
        cents = _entities(claim or "")
        eents = _entities(evidence or "")
        shared = cents & eents

        directional = _directional_reversal(claim or "", evidence or "", shared)
        operator = _operator_divergence(claim or "", evidence or "")
        near_far = bool(shared_n >= 1 and ent >= 0.5 and cov < _NEAR_COV)
        partial_mask = bool(_NEAR_COV <= cov < _FOLD_COV)
        contradiction = bool(f["contradiction_indicator"])

        signals = {
            "content_coverage_claim": cov, "entity_overlap": ent,
            "shared_entities": shared_n,
            "directional_mismatch": directional,
            "operator_mismatch": operator,
            "negation_asymmetry": bool(f["polarity_mismatch"]),
            "antonym_hit": bool(f["antonym_hit"]),
            "numeric_mismatch": bool(f["numeric_mismatch"]),
            "entailment_direction_asymmetry": directional,
            "same_topic_different_relation": near_far,
            "semantic_near_epistemic_far": near_far,
            "lexical_overlap_relation_divergence": bool(cov >= _NEAR_COV and cov < _FOLD_COV),
            "surface_similarity_masking_contradiction": bool(contradiction and cov >= _NEAR_COV),
        }

        # a fold is only "tempting" when there is real surface similarity
        applicable = bool(cov >= _NEAR_COV or (ent >= 0.5 and shared_n >= 1))
        if not applicable:
            return UnfoldResult("fold_safe", False, False, signals,
                                f"low surface similarity (cov={cov}, entity_overlap={ent}); "
                                "not a fold candidate -> defer")

        # precedence among divergence signals
        if contradiction:
            cat, why = "contradiction_masking", (
                "antonym" if f["antonym_hit"] else
                "numeric mismatch" if f["numeric_mismatch"] else "negation asymmetry")
        elif directional:
            cat, why = "directional_divergence", "relation/entity order reversed"
        elif operator:
            cat, why = "operator_divergence", "universal vs existential quantifier"
        elif near_far:
            cat, why = "semantic_near_epistemic_far", (
                f"same topic (entity_overlap={ent}) but different relation (cov={cov})")
        elif partial_mask:
            cat, why = "partial_support_masking", (
                f"claim only partially covered by evidence (cov={cov})")
        else:
            cat, why = "fold_safe", f"high coverage, no divergence (cov={cov}, entity_overlap={ent})"

        return UnfoldResult(cat, cat != "fold_safe", True, signals,
                            f"{cat}: {why}")


__all__ = ["CATEGORIES", "SemanticUnfoldingDetector", "UnfoldResult"]
