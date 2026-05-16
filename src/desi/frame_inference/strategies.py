"""Aufgabe 5 — four inference strategies.

All four are *external wrappers*: they read the chain text and
return a single ``FrameKind`` candidate (or ``None``) without
touching ``FrameDetector`` or any runtime module. The wrapper
in :mod:`desi.frame_inference.wrapper` then turns the candidate
into a synthetic ``Frame:`` marker passed into the frozen
v3.13 routing pipeline.

The vocabularies below are hand-curated; they are deliberately
narrow so that natural prose either matches one frame strongly
or matches none (in which case the strategy returns ``None``
and the chain ends up ``UNDECIDABLE`` downstream — the v4.0
fallback).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..external_probe.corpus import ExternalChain
from ..frames import FrameDetector, FrameKind
from .enums import InferenceStrategy


# Closed per-frame vocabulary. Only the eight non-undeclared
# frames are searchable; FRAME_UNDECLARED is the default for
# ``None`` returns.
_VOCAB: dict[FrameKind, tuple[str, ...]] = {
    FrameKind.EMPIRICAL_CAUSAL: (
        "patient", "patients", "mice", "rats", "cells", "cell",
        "tumor", "tumour", "diagnosis", "imaging", "ct ",
        "ultrasound", "biopsy", "clinical", "drug", "dose",
        "treatment", "infection", "infections", "syndrome",
        "diet", "yield", "reaction", "experiment", "study",
        "trial", "control", "placebo", "sample", "samples",
        "field", "soil", "ecosystem", "stratigraphy", "rainfall",
        "reservoir", "hospital", "patients", "blood", "lab",
        "rate", "rates", "weight", "weights", "concentration",
        "concentrations", "elevated", "reduced", "increased",
        "decreased", "drove", "drives", "led to", "results in",
        "resulted in", "caused", "causes", "due to", "after",
    ),
    FrameKind.FORMAL_LOGIC: (
        "suppose", "let ", "consider ", "theorem", "lemma",
        "corollary", "proof", "integer", "integers", "prime",
        "primes", "sequence", "sequences", "function",
        "functions", "interval", "intervals", "matrix",
        "matrices", "subset", "subsets", "polynomial",
        "polynomials", "rational", "irrational", "convergent",
        "divergent", "continuous", "differentiable", "convex",
        "compact", "modulo", "transitive", "ideal", "ideals",
        "eigenvalue", "eigenvalues", "graph", "graphs",
        "vertex", "vertices", "if and only if", "therefore",
        "thus", "hence", "by definition", "syllogism",
        "statute", "ordinance", "doctrine", "precedent",
        "contract", "tenant", "landlord", "defendant",
        "plaintiff", "constitution", "amendment", "clause",
        "claim", "claims", "burden of", "standard of",
        "statute of limitations", "patent", "copyright",
        "trademark", "lease", "deed", "warrant", "warrants",
        "policy",
    ),
    FrameKind.AUTHORITY_SPEECH: (
        "experts ", "expert ", "specialists", "specialist ",
        "industry voices", "industry ", "commentators",
        "officials ", "official ", "pollsters", "celebrity",
        "celebrities", "endorsed", "endorse", "according to",
        "authorities", "authority", "executives", "executive ",
        "spokesperson", "spokespeople", "advisers", "adviser",
        "consultants", "consultant ", "ministers", "minister ",
        "regulators", "regulator ", "analyst", "analysts",
        "monograph", "treatise", "panel ", "panels ",
        "claimed ", "claims ", "asserts ", "asserted ",
        "declares ", "declared ", "states that",
        "stated that", "said that", "says that", "warned ",
        "voiced ", "voices ", "endorse ", "endorsed ",
    ),
    FrameKind.METAPHORICAL: (
        "like a ", "like an ", "as if ", "as though ",
        "metaphor", "metaphorical", "metaphorically",
        "figuratively", "figurative", "loosely speaking",
        "in a sense", "in some sense", "imagery", "analogy",
        "analogous", "is essentially", "is basically",
        "tidal rhythm", "boulder", "engine", "fire",
        "kindling", "lattice", "spark", "tide", "current",
    ),
    FrameKind.TOOL_COMPUTABLE: (
        "compute ", "calculate ", "calculation", "how many",
        "what is the sum", "what is the product",
        "how much", "evaluate ", "sum of ", "product of ",
        "divide ", "subtract ", "addition", "subtraction",
    ),
    FrameKind.THERMODYNAMIC: (
        "joule", "joules", "kelvin", "celsius",
        "heat ", "temperature ", "thermodynamic",
        "thermodynamics", "enthalpy", "entropy ",
        "free energy", "boltzmann",
    ),
    FrameKind.INFORMATION_THEORETIC: (
        "bits ", "bit ", "shannon", "mutual information",
        "channel capacity", "kolmogorov", "compression",
        "encoding", "code length", "information-theoretic",
        "information theoretic",
    ),
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: (
        "same object", "distinguishable",
        "indistinguishable", "numerically identical",
        "identity of", "ontologically", "qualitatively identical",
    ),
}


def _scan_vocab(text: str) -> dict[FrameKind, int]:
    low = " " + text.lower() + " "
    scores: dict[FrameKind, int] = {}
    for kind, vocab in _VOCAB.items():
        hits = 0
        for term in vocab:
            # All vocab terms include surrounding whitespace
            # markers or punctuation as authored; matching is a
            # literal substring search on the padded text.
            if term in low:
                hits += 1
        if hits:
            scores[kind] = hits
    return scores


def _split_sentences(text: str) -> tuple[str, ...]:
    out: list[str] = []
    chunk = ""
    for ch in text:
        chunk += ch
        if ch in ".!?":
            stripped = chunk.strip()
            if stripped:
                out.append(stripped)
            chunk = ""
    tail = chunk.strip()
    if tail:
        out.append(tail)
    return tuple(out)


# ----- F1 marker-only lexical ----------------------------------

def f1_marker_lexical(chain: ExternalChain) -> FrameKind | None:
    """Run the v3.4 ``FrameDetector`` on the chain text. Return
    its declared frame (if any), else ``None``. This strategy
    pure-wraps the detector and is the v4.0 baseline behaviour
    when ``inherited_context_text`` is empty.
    """
    detector = FrameDetector()
    decl = detector.detect(
        claim_id=chain.chain_id, source_text=chain.text,
    )
    if decl.frame_kind is FrameKind.FRAME_UNDECLARED:
        return None
    return decl.frame_kind


# ----- F2 semantic nearest-neighbour ---------------------------

_F2_MIN_MARGIN: int = 2
_F2_MIN_HITS: int = 2


def f2_nearest_neighbor(chain: ExternalChain) -> FrameKind | None:
    """Score every frame's vocabulary against the chain text.
    Return the frame with the highest score *if* it beats the
    runner-up by ``_F2_MIN_MARGIN`` hits and itself reaches
    ``_F2_MIN_HITS``, else ``None``. Ties produce ``None`` —
    the strategy refuses to commit when evidence is ambiguous.
    """
    scores = _scan_vocab(chain.text)
    if not scores:
        return None
    ordered = sorted(
        scores.items(), key=lambda kv: (-kv[1], kv[0].value),
    )
    best_kind, best_score = ordered[0]
    if best_score < _F2_MIN_HITS:
        return None
    if len(ordered) == 1:
        return best_kind
    _, second_score = ordered[1]
    if best_score - second_score < _F2_MIN_MARGIN:
        return None
    return best_kind


# ----- F3 sentence-local co-occurrence ------------------------

_F3_MIN_SUPPORTING_SENTENCES: int = 2
_F3_MIN_SHARE: float = 0.6


def f3_sentence_cooccurrence(
    chain: ExternalChain,
) -> FrameKind | None:
    """For each sentence in the chain, scan vocabularies and
    record the locally-dominant frame. Return the frame that
    dominates at least ``_F3_MIN_SUPPORTING_SENTENCES`` sentences
    and accounts for ``_F3_MIN_SHARE`` of all sentence votes.
    Otherwise return ``None``.
    """
    sentences = _split_sentences(chain.text)
    votes: dict[FrameKind, int] = {}
    for s in sentences:
        s_scores = _scan_vocab(s)
        if not s_scores:
            continue
        local = sorted(
            s_scores.items(), key=lambda kv: (-kv[1], kv[0].value),
        )
        leader, leader_score = local[0]
        if len(local) > 1 and local[1][1] == leader_score:
            # Tied within the sentence — no vote.
            continue
        votes[leader] = votes.get(leader, 0) + 1
    if not votes:
        return None
    total_votes = sum(votes.values())
    ordered = sorted(
        votes.items(), key=lambda kv: (-kv[1], kv[0].value),
    )
    leader, leader_votes = ordered[0]
    if leader_votes < _F3_MIN_SUPPORTING_SENTENCES:
        return None
    if leader_votes / total_votes < _F3_MIN_SHARE:
        return None
    return leader


# ----- F4 context-window inheritance --------------------------

_F4_WINDOW_SIZE: int = 4
_F4_MIN_AGREEMENT: int = 3


@dataclass(frozen=True)
class ContextWindowState:
    """Per-strategy state used by ``f4_context_window`` when
    iterating over the corpus. Reset between strategy runs."""

    domain: str
    history: tuple[FrameKind, ...]


def f4_context_window(
    chain: ExternalChain,
    *,
    prior_history: tuple[tuple[str, FrameKind | None], ...],
) -> FrameKind | None:
    """First call F2 on the chain text. If F2 returns a frame,
    use it. Otherwise look at the last ``_F4_WINDOW_SIZE`` chains
    *in the same domain*; if at least ``_F4_MIN_AGREEMENT`` of
    them resolved to the same frame, inherit that frame.

    ``prior_history`` is a tuple of (domain, frame_or_none) for
    the chains processed before this one. The driver in
    :mod:`runner` is responsible for accumulating it; the
    function itself is stateless so it remains deterministic
    and replay-stable.
    """
    own = f2_nearest_neighbor(chain)
    if own is not None:
        return own
    # Slice prior history to the same domain only.
    same_domain = tuple(
        f for (d, f) in prior_history
        if d == chain.domain.value and f is not None
    )
    if len(same_domain) < _F4_MIN_AGREEMENT:
        return None
    window = same_domain[-_F4_WINDOW_SIZE:]
    counts: dict[FrameKind, int] = {}
    for f in window:
        counts[f] = counts.get(f, 0) + 1
    ordered = sorted(
        counts.items(), key=lambda kv: (-kv[1], kv[0].value),
    )
    leader, leader_count = ordered[0]
    if leader_count < _F4_MIN_AGREEMENT:
        return None
    return leader


# ----- Strategy registry --------------------------------------

StrategyFn = Callable[[ExternalChain], FrameKind | None]

_STATELESS_STRATEGIES: dict[InferenceStrategy, StrategyFn] = {
    InferenceStrategy.F1_MARKER_LEXICAL:        f1_marker_lexical,
    InferenceStrategy.F2_NEAREST_NEIGHBOR:      f2_nearest_neighbor,
    InferenceStrategy.F3_SENTENCE_COOCCURRENCE: f3_sentence_cooccurrence,
}


def is_context_strategy(strategy: InferenceStrategy) -> bool:
    return strategy is InferenceStrategy.F4_CONTEXT_WINDOW


def stateless_strategy(
    strategy: InferenceStrategy,
) -> StrategyFn:
    if strategy not in _STATELESS_STRATEGIES:
        raise KeyError(
            f"{strategy.value} is not a stateless strategy"
        )
    return _STATELESS_STRATEGIES[strategy]


__all__ = [
    "ContextWindowState",
    "StrategyFn",
    "f1_marker_lexical",
    "f2_nearest_neighbor",
    "f3_sentence_cooccurrence",
    "f4_context_window",
    "is_context_strategy",
    "stateless_strategy",
]
