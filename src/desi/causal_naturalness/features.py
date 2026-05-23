"""Aufgabe 1 — per-chain naturalness feature vector.

Eight closed features per chain. All features are
deterministic, lexical, and free of any LLM call. The vector
is the only object downstream metrics depend on.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..causal_link_typing.classifier import classify_link
from ..causal_link_typing.enums import CorpusSource, LinkType
from ..causal_link_typing.extractor import Link, _sentences


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
})


# Per-class marker dictionaries (re-used from causal_link_typing
# but kept locally so this module is self-contained for the
# entropy / density computations).
_MARKER_CLASSES: dict[str, tuple[str, ...]] = {
    "negation": (
        " not ", "n't ", " never ", " none ", " no ",
        " lacked ", " lacks ", " absent ", " vanished ",
        " missing ", " ceased ", " infertile ", " gone ",
    ),
    "quantifier": (
        " all ", " every ", " some ", " any ", " each ",
        " consistently ", " universally ", " throughout ",
        " invariably ", " always ", " globally ",
    ),
    "cycle_connective": (
        " because ", " depends on ", " requires ", " relies on ",
        " uses ", " rests on ", " follows from ", " stems from ",
        " comes from ", " stands on ", " leans against ",
        " emerges from ", " grows from ",
    ),
    "authority": (
        " says ", " said ", " states ", " stated ", " claims ",
        " claimed ", " declares ", " declared ", " concludes ",
        " concluded ", " announces ", " announced ",
        " reports ", " reported ",
        " wrote ", " writes ", " argued ", " argues ",
        " noted ", " notes ", " thought ", " thinks ",
        " felt ", " feels ", " suggested ", " suggests ",
        " believed ", " believes ", " according to ",
    ),
    "metaphor": (
        " is a ", " is an ", " are a ", " are an ",
        " like a ", " as if ", " loosely speaking ",
        " metaphorically ", " figuratively ",
    ),
    "tool": (
        " + ", " - ", " * ", " / ", " = ",
        "compute", "calculate", "calculation",
    ),
}


def _content_tokens(text: str) -> list[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    out: list[str] = []
    for tok in s.split():
        if tok in _STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        out.append(tok)
    return out


def _marker_counts(text: str) -> dict[str, int]:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        padded = padded.replace(ch, " ")
    out: dict[str, int] = {}
    for cls, markers in _MARKER_CLASSES.items():
        c = sum(padded.count(m) for m in markers)
        if c:
            out[cls] = c
    return out


def _sentences_chain(text: str) -> tuple[str, ...]:
    return _sentences(text)


def _chain_links(chain_id: str, text: str,
                 corpus: CorpusSource) -> tuple[Link, ...]:
    sents = _sentences_chain(text)
    out: list[Link] = []
    for i in range(len(sents) - 1):
        out.append(Link(
            chain_id=chain_id, corpus=corpus, index=i,
            source_text=sents[i], target_text=sents[i + 1],
        ))
    return tuple(out)


@dataclass(frozen=True)
class NaturalnessVector:
    chain_id: str
    corpus: str
    marker_density: float
    marker_entropy: float
    lexical_redundancy: float
    synonym_stacking: float
    transition_variance: float
    frame_switch_frequency: float
    unknown_link_ratio: float
    explicitness_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "corpus": self.corpus,
            "marker_density": self.marker_density,
            "marker_entropy": self.marker_entropy,
            "lexical_redundancy": self.lexical_redundancy,
            "synonym_stacking": self.synonym_stacking,
            "transition_variance": self.transition_variance,
            "frame_switch_frequency": self.frame_switch_frequency,
            "unknown_link_ratio": self.unknown_link_ratio,
            "explicitness_score": self.explicitness_score,
        }

    def feature_tuple(self) -> tuple[float, ...]:
        return (
            self.marker_density,
            self.marker_entropy,
            self.lexical_redundancy,
            self.synonym_stacking,
            self.transition_variance,
            self.frame_switch_frequency,
            self.unknown_link_ratio,
            self.explicitness_score,
        )


_EXPLICITNESS_WEIGHTS: dict[str, float] = {
    "negation":         1.0,
    "quantifier":       1.5,
    "cycle_connective": 1.5,
    "authority":        2.0,
    "metaphor":         2.0,
    "tool":             1.0,
}


def compute_vector(chain_id: str, text: str,
                   corpus: CorpusSource) -> NaturalnessVector:
    sents = _sentences_chain(text)
    if len(sents) < 1:
        return NaturalnessVector(
            chain_id=chain_id, corpus=corpus.value,
            marker_density=0.0, marker_entropy=0.0,
            lexical_redundancy=0.0, synonym_stacking=0.0,
            transition_variance=0.0, frame_switch_frequency=0.0,
            unknown_link_ratio=0.0, explicitness_score=0.0,
        )

    # Tokenisation per sentence.
    sent_tokens = [_content_tokens(s) for s in sents]
    all_tokens = [t for sub in sent_tokens for t in sub]
    total = len(all_tokens) or 1

    # Marker counts per sentence (already class-bucketed).
    sent_marker_counts = [_marker_counts(s) for s in sents]

    # 1. marker_density.
    marker_total = sum(
        sum(c.values()) for c in sent_marker_counts
    )
    marker_density = round(marker_total / total, 6)

    # 2. marker_entropy (Shannon over classes, base 2).
    cls_totals: dict[str, int] = {}
    for c in sent_marker_counts:
        for k, v in c.items():
            cls_totals[k] = cls_totals.get(k, 0) + v
    cls_sum = sum(cls_totals.values())
    if cls_sum > 0:
        entropy = -sum(
            (v / cls_sum) * math.log2(v / cls_sum)
            for v in cls_totals.values() if v > 0
        )
    else:
        entropy = 0.0
    marker_entropy = round(entropy, 6)

    # 3. lexical_redundancy: tokens appearing 2+ times / total.
    freq: dict[str, int] = {}
    for t in all_tokens:
        freq[t] = freq.get(t, 0) + 1
    repeated = sum(c for c in freq.values() if c >= 2)
    lexical_redundancy = round(repeated / total, 6)

    # 4. synonym_stacking: pairs of adjacent sentences sharing
    # the same marker class.
    stacking = 0
    adjacent_pairs = 0
    for i in range(len(sent_marker_counts) - 1):
        adjacent_pairs += 1
        a_classes = set(sent_marker_counts[i])
        b_classes = set(sent_marker_counts[i + 1])
        if a_classes & b_classes:
            stacking += 1
    synonym_stacking = (
        round(stacking / adjacent_pairs, 6) if adjacent_pairs else 0.0
    )

    # 5. transition_variance: variance of sentence-pair lexical
    # distances (1 - jaccard token overlap).
    distances: list[float] = []
    for i in range(len(sent_tokens) - 1):
        a, b = set(sent_tokens[i]), set(sent_tokens[i + 1])
        union = a | b
        inter = a & b
        d = 1.0 - (len(inter) / len(union) if union else 0.0)
        distances.append(d)
    if len(distances) >= 2:
        mu = sum(distances) / len(distances)
        var = sum((x - mu) ** 2 for x in distances) / len(distances)
        transition_variance = round(var, 6)
    else:
        transition_variance = 0.0

    # 6. frame_switch_frequency: switches between LinkType classes
    # across adjacent links.
    links = _chain_links(chain_id, text, corpus)
    link_types = [classify_link(l).value for l in links]
    switches = sum(
        1 for i in range(len(link_types) - 1)
        if link_types[i] != link_types[i + 1]
    )
    frame_switch_frequency = (
        round(switches / len(link_types), 6) if link_types else 0.0
    )

    # 7. unknown_link_ratio.
    unknown_count = sum(
        1 for t in link_types if t == LinkType.UNKNOWN.value
    )
    unknown_link_ratio = (
        round(unknown_count / len(link_types), 6)
        if link_types else 0.0
    )

    # 8. explicitness_score.
    explicit = 0.0
    for cls, w in _EXPLICITNESS_WEIGHTS.items():
        explicit += cls_totals.get(cls, 0) * w
    # Normalise by total content tokens so longer chains do not
    # automatically score higher.
    explicitness_score = round(explicit / total, 6)

    return NaturalnessVector(
        chain_id=chain_id,
        corpus=corpus.value,
        marker_density=marker_density,
        marker_entropy=marker_entropy,
        lexical_redundancy=lexical_redundancy,
        synonym_stacking=synonym_stacking,
        transition_variance=transition_variance,
        frame_switch_frequency=frame_switch_frequency,
        unknown_link_ratio=unknown_link_ratio,
        explicitness_score=explicitness_score,
    )


__all__ = [
    "NaturalnessVector",
    "compute_vector",
]
