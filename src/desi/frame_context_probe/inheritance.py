"""Aufgabe 4 — context-inheritance simulator.

Simulates frame inheritance over the 4-layer context window by
scanning each layer for known context signals and resolving the
highest-priority signal.

Priority order (Aufgabe 4):

    EXPLICIT_FRAME > SECTION_HEADER > DOMAIN_REPETITION > NONE

The real ``FrameDetector`` is **not** touched. This module is a
diagnostic that re-computes a candidate frame purely from the
deterministic context-window fixtures attached by the extractor.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind
from .extractor import ContextWindow, TargetCase
from .signals import ContextSignal


# Lower number = higher priority. NONE is the sentinel and always
# loses against anything else.
_PRIORITY: dict[ContextSignal, int] = {
    ContextSignal.EXPLICIT_FRAME:   0,
    ContextSignal.SECTION_HEADER:   1,
    ContextSignal.DOMAIN_REPETITION: 2,
    ContextSignal.TOOL_ROUTE:        3,
    ContextSignal.AUTHORITY_CONTEXT: 3,
    ContextSignal.METAPHOR_CONTEXT:  3,
    ContextSignal.NONE:              99,
}


# Token → frame mapping for explicit "Frame: <name>" markers.
_EXPLICIT_FRAME_PHRASES: tuple[tuple[str, FrameKind], ...] = (
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


# Token → frame mapping for "Section: …" headers.
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


# Domain-repetition signal: any layer that mentions at least two
# of these frame-anchored tokens together. Deliberately small and
# disjoint per frame — overlap would create silent collisions.
_DOMAIN_TOKENS: dict[FrameKind, tuple[str, ...]] = {
    FrameKind.THERMODYNAMIC: (
        "heat", "kelvin", "joule", "thermodynamic", "isolated system",
    ),
    FrameKind.INFORMATION_THEORETIC: (
        "shannon", "bit", "bits", "channel", "coding",
        "mutual information",
    ),
    FrameKind.METAPHORICAL: (
        "metaphor", "poem", "poet", "rhetorical", "as if", "like a",
    ),
    FrameKind.FORMAL_LOGIC: (
        "modus ponens", "axiom", "proof", "theorem", "lemma",
    ),
    FrameKind.EMPIRICAL_CAUSAL: (
        "caused", "cause-effect", "observed", "experiment",
    ),
    FrameKind.AUTHORITY_SPEECH: (
        "report", "stated", "according to", "third-party",
    ),
    FrameKind.TOOL_COMPUTABLE: (
        "compute", "arithmetic", "calculator", "numerical",
    ),
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: (
        "identity", "reference", "referential", "distinct",
    ),
}


@dataclass(frozen=True)
class InheritanceTrace:
    """One layer-scan record."""

    layer: str            # "ctx_0" / "ctx_1" / "ctx_2" / "ctx_3"
    signal: ContextSignal
    inferred_frame: FrameKind | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "layer": self.layer,
            "signal": self.signal.value,
            "inferred_frame": (
                self.inferred_frame.value if self.inferred_frame else None
            ),
        }


@dataclass(frozen=True)
class InheritanceResult:
    """Outcome of running the simulator over one context window."""

    case_id: str
    expected_frame: FrameKind
    inherited_frame: FrameKind | None
    winning_signal: ContextSignal
    winning_layer: str | None
    traces: tuple[InheritanceTrace, ...]

    @property
    def correct(self) -> bool:
        return self.inherited_frame is self.expected_frame

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "expected_frame": self.expected_frame.value,
            "inherited_frame": (
                self.inherited_frame.value if self.inherited_frame else None
            ),
            "winning_signal": self.winning_signal.value,
            "winning_layer": self.winning_layer,
            "traces": [t.to_dict() for t in self.traces],
            "correct": self.correct,
        }


def _scan_explicit(text: str) -> FrameKind | None:
    low = text.lower()
    for phrase, frame in _EXPLICIT_FRAME_PHRASES:
        if phrase in low:
            return frame
    return None


def _scan_section(text: str) -> FrameKind | None:
    low = text.lower()
    for phrase, frame in _SECTION_PHRASES:
        if phrase in low:
            return frame
    return None


def _scan_domain_repetition(text: str) -> FrameKind | None:
    low = text.lower()
    best_frame: FrameKind | None = None
    best_hits = 0
    for frame, tokens in _DOMAIN_TOKENS.items():
        hits = sum(1 for t in tokens if t in low)
        if hits >= 2 and hits > best_hits:
            best_hits = hits
            best_frame = frame
    return best_frame


def _classify_layer(text: str) -> tuple[ContextSignal, FrameKind | None]:
    """Return the highest-priority signal present in ``text``."""
    f = _scan_explicit(text)
    if f is not None:
        return (ContextSignal.EXPLICIT_FRAME, f)
    f = _scan_section(text)
    if f is not None:
        return (ContextSignal.SECTION_HEADER, f)
    f = _scan_domain_repetition(text)
    if f is not None:
        return (ContextSignal.DOMAIN_REPETITION, f)
    return (ContextSignal.NONE, None)


_LAYER_NAMES: tuple[str, ...] = ("ctx_0", "ctx_1", "ctx_2", "ctx_3")


def simulate(window: ContextWindow, case_id: str,
             expected_frame: FrameKind) -> InheritanceResult:
    """Scan every layer; resolve by priority then by nearest layer."""
    traces: list[InheritanceTrace] = []
    for name, text in zip(_LAYER_NAMES, window.all_layers()):
        sig, frame = _classify_layer(text)
        traces.append(InheritanceTrace(
            layer=name, signal=sig, inferred_frame=frame,
        ))

    # Pick the trace with the lowest priority number (highest priority);
    # break ties by nearest layer (ctx_0 < ctx_1 < ctx_2 < ctx_3).
    winning_idx: int | None = None
    winning_prio = _PRIORITY[ContextSignal.NONE]
    for idx, tr in enumerate(traces):
        prio = _PRIORITY[tr.signal]
        if tr.inferred_frame is None:
            continue
        if prio < winning_prio:
            winning_prio = prio
            winning_idx = idx

    if winning_idx is None:
        return InheritanceResult(
            case_id=case_id,
            expected_frame=expected_frame,
            inherited_frame=None,
            winning_signal=ContextSignal.NONE,
            winning_layer=None,
            traces=tuple(traces),
        )
    win = traces[winning_idx]
    return InheritanceResult(
        case_id=case_id,
        expected_frame=expected_frame,
        inherited_frame=win.inferred_frame,
        winning_signal=win.signal,
        winning_layer=win.layer,
        traces=tuple(traces),
    )


def simulate_target(case: TargetCase) -> InheritanceResult:
    return simulate(case.context_window, case.case_id, case.expected_frame)


def simulate_all(cases: tuple[TargetCase, ...]) -> tuple[
    InheritanceResult, ...
]:
    return tuple(simulate_target(c) for c in cases)


__all__ = [
    "InheritanceResult",
    "InheritanceTrace",
    "simulate",
    "simulate_all",
    "simulate_target",
]
