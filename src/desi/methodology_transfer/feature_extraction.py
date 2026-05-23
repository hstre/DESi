"""Aufgabe 6 — feature extraction for failure cluster
discovery.

Each chain that DESi audits as a *failure* (audit verdict
disagrees with ground truth) is reduced to a fixed-length
boolean / numeric feature vector. The features are
generic structural / grammatical signals — not domain
words, not v4 marker buckets. The clustering algorithm
operates only on these vectors; it never sees the chain
text directly.

The closed feature schema is exposed as ``FEATURE_NAMES``
so cluster names can be derived from feature centroids
without copying any v4 class identifier.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from ..logic.premises import PremiseExtractor
from .corpus import TransferChain


_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were",
    "of", "to", "in", "on", "at", "and", "or", "for",
    "with", "by", "from", "as", "be", "been",
    "this", "that", "these", "those", "it",
    "therefore", "thus", "so", "hence", "than", "more",
})


_MODAL_TOKENS: frozenset[str] = frozenset({
    "will", "must", "cannot", "should", "would",
    "may", "might", "could", "shall",
})


_NEGATION_SURFACE: frozenset[str] = frozenset({
    "not", "never", "no", "none", "without", "excluded",
    "denied", "absent", "withheld",
})


_UNIVERSAL_SURFACE: frozenset[str] = frozenset({
    "every", "all", "any", "always", "entire",
})


def _content_tokens(text: str) -> set[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        s = s.replace(ch, " ")
    return {
        t for t in s.split()
        if t not in _STOPWORDS and len(t) >= 3
    }


def _all_tokens(text: str) -> set[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        s = s.replace(ch, " ")
    return {t for t in s.split() if len(t) >= 1}


@dataclass(frozen=True)
class FailureSample:
    chain_id: str
    domain: str
    audit_verdict: str  # SUPPORTED / REJECTED / OTHER
    audit_rule: str | None
    expected_label: str  # ground truth
    features: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "audit_verdict": self.audit_verdict,
            "audit_rule": self.audit_rule,
            "expected_label": self.expected_label,
            "features": list(self.features),
        }


# Closed feature schema. The cluster-discovery algorithm
# operates only on these values and never sees the chain
# text directly. None of the names match any v4 closed
# class.
FEATURE_NAMES: tuple[str, ...] = (
    "premise_count",                 # 0
    "concl_token_count",             # 1
    "concl_novel_token_ratio",       # 2 fraction of concl tokens NOT in any premise
    "overlap_premises_count",        # 3 # distinct premises sharing tokens with concl
    "overlap_total_tokens",          # 4 total shared tokens across premises
    "modal_in_concl",                # 5
    "modal_in_any_premise",          # 6
    "negation_in_concl",             # 7
    "negation_in_any_premise",       # 8
    "universal_in_concl",            # 9
    "universal_in_any_premise",      # 10
    "concl_has_ed_suffix_verb",      # 11 morphological past-tense cue in concl
    "premise_has_ed_suffix_verb",    # 12 same in premises
    "audit_supported",               # 13
    "audit_rejected",                # 14
    "expected_valid",                # 15
    "expected_invalid",              # 16
    "expected_ambiguous",            # 17
)


def _has_any_in_tokens(text: str, vocab: frozenset[str]) -> bool:
    return bool(_all_tokens(text) & vocab)


def _has_ed_suffix(text: str) -> bool:
    for tok in _all_tokens(text):
        if len(tok) >= 4 and tok.endswith("ed"):
            return True
    return False


def extract_features(chain: TransferChain) -> FailureSample:
    auditor = LogicalAuditor()
    extractor = PremiseExtractor()
    a = auditor.audit(chain.text)
    e = extractor.extract(chain.text)
    if e.conclusion is None or not e.premises:
        # Degenerate; emit zero-features sample for cluster
        # completeness.
        return FailureSample(
            chain_id=chain.chain_id, domain=chain.domain,
            audit_verdict=a.state.value,
            audit_rule=a.rule.value if a.rule else None,
            expected_label=chain.ground_truth,
            features=(0.0,) * len(FEATURE_NAMES),
        )
    premise_count = len(e.premises)
    concl_tokens = _content_tokens(e.conclusion.text)
    concl_token_count = len(concl_tokens)
    overlap_premises = 0
    overlap_total = 0
    premise_token_union: set[str] = set()
    for p in e.premises:
        pt = _content_tokens(p.text)
        premise_token_union |= pt
        shared = concl_tokens & pt
        if shared:
            overlap_premises += 1
            overlap_total += len(shared)
    novel = concl_tokens - premise_token_union
    novel_ratio = (
        len(novel) / concl_token_count
        if concl_token_count else 0.0
    )
    modal_concl = _has_any_in_tokens(
        e.conclusion.text, _MODAL_TOKENS,
    )
    modal_premise = any(
        _has_any_in_tokens(p.text, _MODAL_TOKENS)
        for p in e.premises
    )
    neg_concl = _has_any_in_tokens(
        e.conclusion.text, _NEGATION_SURFACE,
    )
    neg_premise = any(
        _has_any_in_tokens(p.text, _NEGATION_SURFACE)
        for p in e.premises
    )
    uni_concl = _has_any_in_tokens(
        e.conclusion.text, _UNIVERSAL_SURFACE,
    )
    uni_premise = any(
        _has_any_in_tokens(p.text, _UNIVERSAL_SURFACE)
        for p in e.premises
    )
    ed_concl = _has_ed_suffix(e.conclusion.text)
    ed_premise = any(_has_ed_suffix(p.text) for p in e.premises)
    audit_supported = (
        a.state is LogicalState.LOGICALLY_SUPPORTED
        and a.rule is InferenceRule.CAUSAL_CHAIN
    )
    audit_rejected = (
        a.state is LogicalState.LOGICALLY_REJECTED
    )
    feats = (
        float(premise_count),
        float(concl_token_count),
        novel_ratio,
        float(overlap_premises),
        float(overlap_total),
        float(modal_concl),
        float(modal_premise),
        float(neg_concl),
        float(neg_premise),
        float(uni_concl),
        float(uni_premise),
        float(ed_concl),
        float(ed_premise),
        float(audit_supported),
        float(audit_rejected),
        float(chain.ground_truth == "VALID"),
        float(chain.ground_truth == "INVALID"),
        float(chain.ground_truth == "AMBIGUOUS"),
    )
    return FailureSample(
        chain_id=chain.chain_id, domain=chain.domain,
        audit_verdict=a.state.value,
        audit_rule=a.rule.value if a.rule else None,
        expected_label=chain.ground_truth,
        features=feats,
    )


def is_failure(sample: FailureSample) -> bool:
    """A chain is a *failure* for v5.0 discovery purposes
    when the audit verdict disagrees with the ground-truth
    label in a polarity-meaningful direction:

    * audit SUPPORTED + ground truth INVALID -> false support
    * audit REJECTED + ground truth VALID    -> false block
    * audit SUPPORTED + ground truth AMBIGUOUS -> over-support
    * audit REJECTED + ground truth AMBIGUOUS  -> over-block
    """
    audit_supported = bool(sample.features[13])
    audit_rejected = bool(sample.features[14])
    if sample.expected_label == "VALID":
        return audit_rejected
    if sample.expected_label == "INVALID":
        return audit_supported
    # AMBIGUOUS: either polarity counts as a failure of
    # epistemic restraint.
    return audit_supported or audit_rejected


__all__ = [
    "FEATURE_NAMES", "FailureSample", "extract_features",
    "is_failure",
]
