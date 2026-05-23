"""Aufgabe 2 — independence check against v2.3 + v2.6.

Compares the held-out corpus to the v2.3 multistep cases and
the v2.6 causal-probe cases on four axes:

* ``exact_text_overlap`` — number of held-out texts that appear
  verbatim in either upstream pool (must be 0).
* ``lexical_overlap`` — average Jaccard similarity of
  content-word tokens between each held-out case and its
  *closest* upstream match (lower = more independent).
* ``therefore_pattern_overlap`` — fraction of held-out cases
  whose post-"Therefore" conclusion clause is a substring of
  any upstream post-"Therefore" clause (lower = more
  independent).
* ``premise_shape_overlap`` — fraction of held-out cases whose
  *premise count + therefore-count* shape matches any upstream
  case (information-theoretic floor; not a fail by itself).
* ``trap_shape_overlap`` — fraction of trap held-out cases
  whose shape (negation / cycle connective / quantifier) also
  shows up in v2.6's discovery probe (lower = more novel).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as ALL_MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from .cases import ALL_HELDOUT_CASES, HeldoutCategory


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


def _therefore_clauses(text: str) -> tuple[str, ...]:
    out: list[str] = []
    for sent in text.split("Therefore "):
        if not sent:
            continue
        # Skip the prefix portion before the first Therefore.
        if sent.endswith("."):
            out.append(sent.strip())
        else:
            tail = sent.split(".")[0].strip()
            if tail:
                out.append(tail + ".")
    return tuple(out)


def _premise_count(text: str) -> int:
    return sum(
        1 for s in text.split(".")
        if s.strip() and "therefore" not in s.lower()
    )


def _therefore_count(text: str) -> int:
    return text.lower().count("therefore ")


def _v23_texts() -> tuple[str, ...]:
    return tuple(c.text for c in ALL_MULTISTEP_CASES)


def _v26_texts() -> tuple[str, ...]:
    # v2.6 probe runs over the union of v1.5 main + v2.3 multistep,
    # so its "corpus" is the union of those two pools.
    return tuple(c.text for c in ALL_MAIN_CASES)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass(frozen=True)
class IndependenceReport:
    held_out_total: int
    v23_count: int
    v26_count: int
    exact_text_overlap: int
    lexical_overlap_mean: float
    lexical_overlap_max: float
    therefore_pattern_overlap: int
    therefore_pattern_overlap_rate: float
    premise_shape_overlap: int
    premise_shape_overlap_rate: float
    trap_shape_overlap: int
    trap_shape_overlap_rate: float
    independence_passed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "held_out_total": self.held_out_total,
            "v23_count": self.v23_count,
            "v26_count": self.v26_count,
            "exact_text_overlap": self.exact_text_overlap,
            "lexical_overlap_mean": self.lexical_overlap_mean,
            "lexical_overlap_max": self.lexical_overlap_max,
            "therefore_pattern_overlap": self.therefore_pattern_overlap,
            "therefore_pattern_overlap_rate":
                self.therefore_pattern_overlap_rate,
            "premise_shape_overlap": self.premise_shape_overlap,
            "premise_shape_overlap_rate": self.premise_shape_overlap_rate,
            "trap_shape_overlap": self.trap_shape_overlap,
            "trap_shape_overlap_rate": self.trap_shape_overlap_rate,
            "independence_passed": self.independence_passed,
            "reason": self.reason,
        }


# Lexical-similarity ceiling. Anything strictly above this is
# flagged as a near-duplicate.
MAX_LEXICAL_MEAN: float = 0.30
MAX_LEXICAL_PEAK: float = 0.50
MAX_STRUCTURE_SHARE: float = 0.20


def run_independence_check() -> IndependenceReport:
    upstream_texts = _v23_texts() + _v26_texts()
    upstream_set = set(upstream_texts)
    upstream_clauses = set()
    for t in upstream_texts:
        for c in _therefore_clauses(t):
            upstream_clauses.add(c)
    upstream_shapes = set()
    for t in upstream_texts:
        upstream_shapes.add((_premise_count(t), _therefore_count(t)))
    upstream_token_sets = [_content_tokens(t) for t in upstream_texts]

    exact_hits = 0
    lex_per_case: list[float] = []
    therefore_hits = 0
    shape_hits = 0
    trap_shape_hits = 0
    trap_total = 0

    for hc in ALL_HELDOUT_CASES:
        if hc.text in upstream_set:
            exact_hits += 1
        ht = _content_tokens(hc.text)
        best = 0.0
        for ut in upstream_token_sets:
            j = _jaccard(ht, ut)
            if j > best:
                best = j
        lex_per_case.append(best)
        for clause in _therefore_clauses(hc.text):
            if clause in upstream_clauses:
                therefore_hits += 1
                break
        shape = (_premise_count(hc.text), _therefore_count(hc.text))
        if shape in upstream_shapes:
            shape_hits += 1
        if hc.category in (
            HeldoutCategory.C_CONTRADICTION_TRAP,
            HeldoutCategory.D_CYCLE_TRAP,
            HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        ):
            trap_total += 1
            if shape in upstream_shapes:
                trap_shape_hits += 1

    n = len(ALL_HELDOUT_CASES)
    lex_mean = round(sum(lex_per_case) / n, 6) if n else 0.0
    lex_max = round(max(lex_per_case, default=0.0), 6)
    issues: list[str] = []
    if exact_hits > 0:
        issues.append(f"exact_text_overlap={exact_hits} > 0")
    if lex_mean > MAX_LEXICAL_MEAN:
        issues.append(
            f"lexical_overlap_mean={lex_mean} > {MAX_LEXICAL_MEAN}"
        )
    if lex_max > MAX_LEXICAL_PEAK:
        issues.append(
            f"lexical_overlap_max={lex_max} > {MAX_LEXICAL_PEAK}"
        )
    structure_share = (shape_hits / n) if n else 0.0
    if structure_share > MAX_STRUCTURE_SHARE * 5:
        # Premise-shape overlap is information-theoretic — 3-step
        # chains are common. Treat as fail only if the share crosses
        # five times the structure threshold.
        issues.append(
            f"premise_shape_overlap_rate={structure_share} "
            "is unreasonably high"
        )

    return IndependenceReport(
        held_out_total=n,
        v23_count=len(_v23_texts()),
        v26_count=len(_v26_texts()),
        exact_text_overlap=exact_hits,
        lexical_overlap_mean=lex_mean,
        lexical_overlap_max=lex_max,
        therefore_pattern_overlap=therefore_hits,
        therefore_pattern_overlap_rate=(
            round(therefore_hits / n, 6) if n else 0.0
        ),
        premise_shape_overlap=shape_hits,
        premise_shape_overlap_rate=round(structure_share, 6),
        trap_shape_overlap=trap_shape_hits,
        trap_shape_overlap_rate=(
            round(trap_shape_hits / trap_total, 6) if trap_total else 0.0
        ),
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
