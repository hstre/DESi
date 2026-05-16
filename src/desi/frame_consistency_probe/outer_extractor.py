"""Aufgabe 3 — outer-frame extraction from CTX_1–CTX_3.

Mirrors the v3.8 inheritance simulator's signal grammar but is
restricted to the *outer* layers (the case sentence in CTX_0 is
deliberately excluded so the outer verdict can disagree with the
inner one). Priority order:

    EXPLICIT_FRAME > SECTION_HEADER > DOMAIN_REPETITION > NONE
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind


_EXPLICIT_PHRASES: tuple[tuple[str, FrameKind], ...] = (
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
    ("frame: undeclared",                   FrameKind.FRAME_UNDECLARED),
)


_SECTION_PHRASES: tuple[tuple[str, FrameKind], ...] = (
    ("section: thermodynamics",      FrameKind.THERMODYNAMIC),
    ("section: information theory",  FrameKind.INFORMATION_THEORETIC),
    ("section: ontology",            FrameKind.ONTOLOGICAL_DISTINGUISHABILITY),
    ("section: rhetorical devices",  FrameKind.METAPHORICAL),
    ("section: formal logic",        FrameKind.FORMAL_LOGIC),
    ("section: empirical causality", FrameKind.EMPIRICAL_CAUSAL),
    ("section: speech acts",         FrameKind.AUTHORITY_SPEECH),
    ("section: computation",         FrameKind.TOOL_COMPUTABLE),
    ("section: unframed",            FrameKind.FRAME_UNDECLARED),
)


_DOMAIN_TOKENS: dict[FrameKind, tuple[str, ...]] = {
    FrameKind.THERMODYNAMIC: (
        "heat flow", "kelvin", "joule", "thermodynamic",
        "isolated system",
    ),
    FrameKind.INFORMATION_THEORETIC: (
        "shannon", "bit", "bits", "channel", "coding",
        "mutual information",
    ),
    FrameKind.METAPHORICAL: (
        "metaphor", "poem", "poet", "rhetorical", "as if", "like a",
    ),
    FrameKind.FORMAL_LOGIC: (
        "modus ponens", "axiom", "theorem", "lemma",
    ),
    FrameKind.EMPIRICAL_CAUSAL: (
        "cause-effect", "observed", "experiment",
    ),
    FrameKind.AUTHORITY_SPEECH: (
        "report", "stated", "third-party", "according to",
    ),
    FrameKind.TOOL_COMPUTABLE: (
        "arithmetic", "calculator", "numerical",
    ),
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: (
        "identity", "referential", "reference",
    ),
}


@dataclass(frozen=True)
class OuterTrace:
    layer: str
    signal: str    # explicit_frame / section_header / domain_repetition / none
    frame: FrameKind | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "layer": self.layer,
            "signal": self.signal,
            "frame": self.frame.value if self.frame else None,
        }


@dataclass(frozen=True)
class OuterVerdict:
    frame: FrameKind | None
    signal: str
    layer: str | None
    traces: tuple[OuterTrace, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "frame": self.frame.value if self.frame else None,
            "signal": self.signal,
            "layer": self.layer,
            "traces": [t.to_dict() for t in self.traces],
        }


_PRIORITY: dict[str, int] = {
    "explicit_frame":   0,
    "section_header":   1,
    "domain_repetition": 2,
    "none":             99,
}


def _scan_layer(text: str) -> tuple[str, FrameKind | None]:
    low = text.lower()
    for phrase, frame in _EXPLICIT_PHRASES:
        if phrase in low:
            return ("explicit_frame", frame)
    for phrase, frame in _SECTION_PHRASES:
        if phrase in low:
            return ("section_header", frame)
    best: FrameKind | None = None
    best_hits = 0
    for frame, tokens in _DOMAIN_TOKENS.items():
        hits = sum(1 for t in tokens if t in low)
        if hits >= 2 and hits > best_hits:
            best = frame
            best_hits = hits
    if best is not None:
        return ("domain_repetition", best)
    return ("none", None)


def extract_outer_frame(ctx_1: str, ctx_2: str, ctx_3: str) -> OuterVerdict:
    layers = (("ctx_1", ctx_1), ("ctx_2", ctx_2), ("ctx_3", ctx_3))
    traces: list[OuterTrace] = []
    for name, text in layers:
        sig, frame = _scan_layer(text)
        traces.append(OuterTrace(layer=name, signal=sig, frame=frame))

    winner_idx: int | None = None
    winner_prio = _PRIORITY["none"]
    for idx, tr in enumerate(traces):
        if tr.frame is None:
            continue
        prio = _PRIORITY[tr.signal]
        if prio < winner_prio:
            winner_prio = prio
            winner_idx = idx
    if winner_idx is None:
        return OuterVerdict(
            frame=None, signal="none", layer=None,
            traces=tuple(traces),
        )
    w = traces[winner_idx]
    return OuterVerdict(
        frame=w.frame, signal=w.signal, layer=w.layer,
        traces=tuple(traces),
    )


__all__ = ["OuterTrace", "OuterVerdict", "extract_outer_frame"]
