"""Aufgabe 2 — inner-frame extraction from the case sentence alone.

Deterministic, regex-free, no LLM. Operates **only** on CTX_0
(the sentence itself). The point of running an inner extraction
separate from the inheritance simulator is to make the inner
verdict independent of any inherited outer signal, so that
disagreement can be measured rather than absorbed.
"""
from __future__ import annotations

from ..frames import FrameKind


# Frame-anchored vocabulary; deliberately disjoint and small so a
# single sentence rarely fires two frames at the same strength.
_INNER_TOKENS: dict[FrameKind, tuple[str, ...]] = {
    FrameKind.THERMODYNAMIC: (
        "isolated system", "closed system", "heat flow", "kelvin",
        "joule", "second law", "thermodynamic", "hot to cold",
    ),
    FrameKind.INFORMATION_THEORETIC: (
        "shannon", "bits", "bit", "channel capacity", "channel",
        "mutual information", "coding", "fair coin",
        "message distribution", "nats", "fair die",
    ),
    FrameKind.METAPHORICAL: (
        "poet", "poem", "lover", "smile", "delicate", "like a",
        "as if", "her smile", "his smile", "feathers",
    ),
    FrameKind.FORMAL_LOGIC: (
        "modus ponens", "all swans", "therefore", "axiom",
        "lemma", "theorem", "universal instantiation",
    ),
    FrameKind.EMPIRICAL_CAUSAL: (
        "cause-effect", "caused", "led to", "resulted in",
        "experiment shows", "observed",
    ),
    FrameKind.AUTHORITY_SPEECH: (
        "minister stated", "according to", "report states",
        "third-party", "the minister", "the report",
    ),
    FrameKind.TOOL_COMPUTABLE: (
        "compute", "calculate", "in nats", "in bits", "arithmetic",
        "numerical answer",
    ),
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: (
        "morning star", "evening star", "identity statement",
        "referential", "is identical to",
    ),
}


# Explicit "Frame: <name>" prefixes (the v3.4 detector also
# honours these). We treat them as inner-frame evidence only if
# they literally appear in the case sentence.
_INNER_EXPLICIT: tuple[tuple[str, FrameKind], ...] = (
    ("frame: thermodynamic",                FrameKind.THERMODYNAMIC),
    ("frame: information-theoretic",        FrameKind.INFORMATION_THEORETIC),
    ("frame: information theoretic",        FrameKind.INFORMATION_THEORETIC),
    ("frame: ontological distinguishability",
        FrameKind.ONTOLOGICAL_DISTINGUISHABILITY),
    ("frame: metaphorical",                 FrameKind.METAPHORICAL),
    ("frame: formal logic",                 FrameKind.FORMAL_LOGIC),
    ("frame: empirical causal",             FrameKind.EMPIRICAL_CAUSAL),
    ("frame: authority",                    FrameKind.AUTHORITY_SPEECH),
    ("frame: tool computable",              FrameKind.TOOL_COMPUTABLE),
)


def extract_inner_frame(sentence: str) -> FrameKind | None:
    """Return the inner frame implied by the sentence itself, or
    ``None`` if no frame-specific vocabulary is present.

    Resolution order:

    1. explicit ``Frame: …`` prefix anywhere in the sentence;
    2. otherwise, the frame whose token set has the most hits,
       provided the lead is strict (no tie); ties → ``None``.
    """
    low = sentence.lower()
    for phrase, frame in _INNER_EXPLICIT:
        if phrase in low:
            return frame
    counts: dict[FrameKind, int] = {}
    for frame, tokens in _INNER_TOKENS.items():
        hits = sum(1 for t in tokens if t in low)
        if hits > 0:
            counts[frame] = hits
    if not counts:
        return None
    best = max(counts.values())
    leaders = [f for f, c in counts.items() if c == best]
    if len(leaders) != 1:
        return None
    return leaders[0]


__all__ = ["extract_inner_frame"]
