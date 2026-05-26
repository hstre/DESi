"""Residual semantic escalation (PERIPHERAL, benchmark adapter).

Architecture-first principle from the prior studies: handle most items with the
deterministic algorithmic layers (micro-router + unfolding protection); escalate
ONLY the unresolved / dangerous residue to a lightweight semantic analysis.

Escalate ONLY if a fold is tempting AND the deterministic signals are ambiguous:
the unfolding category is one of {semantic_near_epistemic_far, partial_support_
masking, operator_divergence} or a borderline fold_safe. Clear cases (a hard
contradiction, a clean directional reversal, a high-coverage fold, or a non-fold-
candidate) are resolved deterministically and never escalated.

Residual semantic layer (escalated cases only): deterministic, no LLM, no
chain-of-thought, no iterative prompting, no benchmark prompts. It uses LIGHTWEIGHT
local semantic vectors -- synonym-group term-frequency and character-trigram term-
frequency -- with cosine similarity and *directional (asymmetric) containment*.
NOTE: no learned neural embeddings are available offline in this environment
(no torch / transformers / sentence-transformers / HF token), so the 'vectors'
are deterministic local lexical-semantic vectors. This is documented as a
constraint, not hidden. The vectors are used to detect dangerous false folds,
directional mismatch, and semantic-near/epistemic-far structure -- NOT for naive
folding.

Resolution outcomes -> solver policy:
    fold_safe_confirmed           -> entailment_direct
    directional_entailment_confirmed -> entailment_direct
    semantic_divergence_confirmed -> evidence_strict
    partial_support_confirmed     -> evidence_strict
    unresolved_high_risk          -> baseline (protected)

Deterministic / replay-stable; does NOT import or modify the DESi core.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from micro_semantic_router import (
    MicroSemanticRouter, _STOP, _group, _raw_tokens, _stem,
)
from semantic_unfolding import SemanticUnfoldingDetector

OUTCOMES = (
    "fold_safe_confirmed", "directional_entailment_confirmed",
    "semantic_divergence_confirmed", "partial_support_confirmed",
    "unresolved_high_risk",
)
_OUTCOME_POLICY = {
    "fold_safe_confirmed": "entailment_direct",
    "directional_entailment_confirmed": "entailment_direct",
    "semantic_divergence_confirmed": "evidence_strict",
    "partial_support_confirmed": "evidence_strict",
    "unresolved_high_risk": "baseline",
}


def _group_tf(text: str) -> Counter:
    c = Counter()
    for tok in _raw_tokens(text or ""):
        if tok.lower() in _STOP:
            continue
        st = _stem(tok)
        if len(st) <= 1 and not st.isdigit():
            continue
        c[_group(st)] += 1
    return c


def _char_tf(text: str, n: int = 3) -> Counter:
    s = "".join(ch.lower() if (ch.isalnum() or ch == " ") else " " for ch in (text or ""))
    s = " " + " ".join(s.split()) + " "
    return Counter(s[i:i + n] for i in range(len(s) - n + 1)) if len(s) >= n else Counter()


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a if k in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return round(dot / (na * nb), 3) if na and nb else 0.0


def _containment(a: Counter, b: Counter) -> float:
    """Fraction of a's mass also present in b (directional)."""
    tot = sum(a.values())
    if not tot:
        return 0.0
    return sum(min(a[k], b.get(k, 0)) for k in a) / tot


def _e_policy(unf, micro_policy: str) -> str:
    """E (unfolding-aware) policy -- single source kept identical to the study."""
    if not unf.applicable:
        return micro_policy
    if unf.category == "fold_safe":
        return "entailment_direct"
    if unf.category == "contradiction_masking":
        return "baseline"
    return "evidence_strict"


def _escalate(unf) -> bool:
    """Escalate only the ambiguous residue of fold candidates."""
    if not unf.applicable:
        return False
    cov = unf.signals["content_coverage_claim"]
    if unf.category in ("semantic_near_epistemic_far", "partial_support_masking",
                        "operator_divergence"):
        return True
    if unf.category == "fold_safe" and 0.85 <= cov < 0.95:
        return True
    return False


class ResidualScorer:
    """Deterministic lightweight semantic scorer (synonym-group + char-trigram TF)."""

    def score(self, claim: str, evidence: str, sig: dict) -> dict:
        cg, eg = _group_tf(claim), _group_tf(evidence)
        cc, ec = _char_tf(claim), _char_tf(evidence)
        fwd = round(0.5 * _containment(cg, eg) + 0.5 * _containment(cc, ec), 3)
        bwd = round(0.5 * _containment(eg, cg) + 0.5 * _containment(ec, cc), 3)
        return {
            "char_cosine": _cosine(cc, ec),
            "group_cosine": _cosine(cg, eg),
            "dir_fwd": fwd, "dir_bwd": bwd, "asym": round(fwd - bwd, 3),
            "entity_overlap": sig["entity_overlap"], "shared_entities": sig["shared_entities"],
            "contradiction": bool(sig.get("antonym_hit") or sig.get("numeric_mismatch")),
        }


def resolve(scores: dict) -> tuple[str, str]:
    """Map residual semantic scores -> (outcome, solver policy).

    Directional containment (dir_fwd: how much of the claim is contained in the
    evidence, blended group+char vectors) is the primary axis; entity sharing
    distinguishes same-topic-different-relation from plain low overlap."""
    if scores["contradiction"]:
        out = "unresolved_high_risk"
    elif scores["dir_fwd"] >= 0.8:
        out = ("directional_entailment_confirmed" if scores["asym"] >= 0.1
               else "fold_safe_confirmed")
    elif scores["dir_fwd"] >= 0.45:
        out = "partial_support_confirmed"
    elif scores["shared_entities"] >= 1:
        out = "semantic_divergence_confirmed"
    else:
        out = "unresolved_high_risk"
    return out, _OUTCOME_POLICY[out]


@dataclass(frozen=True)
class ResidualDecision:
    micro_mode: str
    micro_policy: str
    unfold_category: str
    unfold_applicable: bool
    e_policy: str
    escalated: bool
    outcome: str | None
    f_policy: str
    scores: dict | None
    reason: str


class ResidualEscalationRouter:
    """Algorithm-first router with semantic escalation for the residue only."""

    def __init__(self) -> None:
        self._micro = MicroSemanticRouter()
        self._unfold = SemanticUnfoldingDetector()
        self._scorer = ResidualScorer()

    def route(self, claim: str, evidence: str) -> ResidualDecision:
        mres = self._micro.route(claim, evidence)
        unf = self._unfold.detect(claim, evidence)
        ep = _e_policy(unf, mres.policy)
        if _escalate(unf):
            sc = self._scorer.score(claim, evidence, unf.signals)
            outcome, fp = resolve(sc)
            reason = (f"escalated [{unf.category}, dir_fwd={sc['dir_fwd']}, "
                      f"asym={sc['asym']}, char_cos={sc['char_cosine']}] -> {outcome} -> {fp}")
            return ResidualDecision(mres.mode, mres.policy, unf.category, unf.applicable,
                                    ep, True, outcome, fp, sc, reason)
        return ResidualDecision(mres.mode, mres.policy, unf.category, unf.applicable,
                                ep, False, None, ep, None,
                                f"not escalated [{unf.category}] -> deterministic -> {ep}")


__all__ = [
    "OUTCOMES", "ResidualDecision", "ResidualEscalationRouter", "ResidualScorer",
    "resolve",
]
