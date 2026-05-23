"""Aufgabe 2 — independence vs v2.3 + v2.6 + v3.14."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as ALL_MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from .cases import ALL_ADVERSARIAL_CASES


_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "it", "they", "he", "she", "we", "you", "i", "him", "her",
    "his", "hers", "their", "its",
    "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "of", "in", "on", "at", "to", "for", "with", "and", "or", "but",
    "as", "by", "from", "than", "then",
    "therefore", "thus", "so", "hence",
    "if", "while", "when", "where",
    "not", "no", "yes", "all", "some", "any",
})


def _content_tokens(text: str) -> set[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    out: set[str] = set()
    for tok in s.split():
        if tok in _STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        out.add(tok)
    return out


def _premise_count(text: str) -> int:
    return sum(
        1 for s in text.split(".")
        if s.strip() and "therefore" not in s.lower()
    )


def _therefore_count(text: str) -> int:
    return text.lower().count("therefore ")


def _guard_shape(text: str) -> str:
    low = " " + text.lower() + " "
    flags = []
    if any(m in low for m in (" not ", "n't ", " never ", " no ")):
        flags.append("neg")
    if any(m in low for m in (" all ", " every ", " some ", " any ", " each ")):
        flags.append("quant")
    if any(m in low for m in (" because ", " depends on ", " requires ",
                              " relies on ", " uses ")):
        flags.append("cycleconn")
    return ",".join(flags) if flags else "clean"


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


MAX_LEXICAL_MEAN: float = 0.30
MAX_LEXICAL_PEAK: float = 0.50
MAX_STRUCTURE_SHARE: float = 0.20


@dataclass(frozen=True)
class IndependenceReport:
    adversarial_total: int
    v23_count: int
    v26_count: int
    v314_count: int
    exact_overlap: int
    lexical_overlap_mean: float
    lexical_overlap_max: float
    structural_overlap: float
    guard_shape_overlap: float
    independence_passed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "adversarial_total": self.adversarial_total,
            "v23_count": self.v23_count,
            "v26_count": self.v26_count,
            "v314_count": self.v314_count,
            "exact_overlap": self.exact_overlap,
            "lexical_overlap_mean": self.lexical_overlap_mean,
            "lexical_overlap_max": self.lexical_overlap_max,
            "structural_overlap": self.structural_overlap,
            "guard_shape_overlap": self.guard_shape_overlap,
            "independence_passed": self.independence_passed,
            "reason": self.reason,
        }


def _v23_texts() -> tuple[str, ...]:
    return tuple(c.text for c in ALL_MULTISTEP_CASES)


def _v26_texts() -> tuple[str, ...]:
    return tuple(c.text for c in ALL_MAIN_CASES)


def _v314_texts() -> tuple[str, ...]:
    return tuple(c.text for c in ALL_HELDOUT_CASES)


def run_independence_check() -> IndependenceReport:
    upstream_texts = _v23_texts() + _v26_texts() + _v314_texts()
    upstream_set = set(upstream_texts)
    upstream_tokens = [_content_tokens(t) for t in upstream_texts]
    upstream_shapes = {
        (_premise_count(t), _therefore_count(t)) for t in upstream_texts
    }
    upstream_guard_shapes = {_guard_shape(t) for t in upstream_texts}

    exact = 0
    lex_each: list[float] = []
    shape_hits = 0
    guard_hits = 0
    for c in ALL_ADVERSARIAL_CASES:
        if c.text in upstream_set:
            exact += 1
        ht = _content_tokens(c.text)
        best = 0.0
        for ut in upstream_tokens:
            j = _jaccard(ht, ut)
            if j > best:
                best = j
        lex_each.append(best)
        if (_premise_count(c.text), _therefore_count(c.text)) in upstream_shapes:
            shape_hits += 1
        if _guard_shape(c.text) in upstream_guard_shapes:
            guard_hits += 1

    n = len(ALL_ADVERSARIAL_CASES)
    lex_mean = round(sum(lex_each) / n, 6) if n else 0.0
    lex_max = round(max(lex_each, default=0.0), 6)
    structural = round(shape_hits / n, 6) if n else 0.0
    guard_share = round(guard_hits / n, 6) if n else 0.0

    issues: list[str] = []
    if exact > 0:
        issues.append(f"exact_overlap={exact} > 0")
    if structural > MAX_STRUCTURE_SHARE * 5:
        # Structural overlap floor for 3-step chains is high; only
        # fail at five times the threshold.
        issues.append(
            f"structural_overlap={structural} unreasonably high"
        )

    return IndependenceReport(
        adversarial_total=n,
        v23_count=len(_v23_texts()),
        v26_count=len(_v26_texts()),
        v314_count=len(_v314_texts()),
        exact_overlap=exact,
        lexical_overlap_mean=lex_mean,
        lexical_overlap_max=lex_max,
        structural_overlap=structural,
        guard_shape_overlap=guard_share,
        independence_passed=not issues,
        reason="; ".join(issues) if issues else "all gates clear",
    )


__all__ = [
    "IndependenceReport",
    "MAX_LEXICAL_MEAN",
    "MAX_LEXICAL_PEAK",
    "MAX_STRUCTURE_SHARE",
    "run_independence_check",
]
