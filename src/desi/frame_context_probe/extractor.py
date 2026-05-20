"""Target extraction + per-case context windows — Aufgaben 1 + 2.

Pulls every entropy-bearing case from v3.4 / v3.5 / v3.6 corpora
(failures, correct conflicts, correct classifications) and attaches
a deterministic four-layer context window:

* ``CTX_0`` — the case sentence itself
* ``CTX_1`` — synthetic prior sentence (deterministic fixture)
* ``CTX_2`` — section header derived from the group's expected frame
* ``CTX_3`` — document-level frame marker
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from datetime import datetime, timezone

from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_failure_audit import (
    NEGATIVE_CONTROLS as FA_NCS,
    build_audit_report,
)
from ..frame_invariance import (
    ALL_GROUPS as INV_GROUPS,
    NEGATIVE_CONTROLS as INV_NCS,
)
from ..frames import FrameKind


@dataclass(frozen=True)
class ContextWindow:
    ctx_0: str   # the case sentence itself
    ctx_1: str   # prior sentence
    ctx_2: str   # section header
    ctx_3: str   # document frame

    def all_layers(self) -> tuple[str, ...]:
        return (self.ctx_0, self.ctx_1, self.ctx_2, self.ctx_3)

    def to_dict(self) -> dict[str, str]:
        return {
            "ctx_0": self.ctx_0,
            "ctx_1": self.ctx_1,
            "ctx_2": self.ctx_2,
            "ctx_3": self.ctx_3,
        }


# Per-frame fixture: deterministic section header + document frame
# string. Used as CTX_2 / CTX_3 when a target case has no
# specific document context attached.
_FIXTURE_HEADER: dict[FrameKind, str] = {
    FrameKind.THERMODYNAMIC:
        "Section: Thermodynamics — Heat and Energy",
    FrameKind.INFORMATION_THEORETIC:
        "Section: Information Theory — Coding and Bits",
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY:
        "Section: Ontology — Identity and Reference",
    FrameKind.METAPHORICAL:
        "Section: Rhetorical Devices — Metaphor and Simile",
    FrameKind.FORMAL_LOGIC:
        "Section: Formal Logic — Proof Theory",
    FrameKind.EMPIRICAL_CAUSAL:
        "Section: Empirical Causality — Cause and Effect",
    FrameKind.AUTHORITY_SPEECH:
        "Section: Speech Acts — Reported Statements",
    FrameKind.TOOL_COMPUTABLE:
        "Section: Computation — Arithmetic and Dates",
    FrameKind.FRAME_UNDECLARED:
        "Section: Unframed — No frame declared",
}


_FIXTURE_DOC_FRAME: dict[FrameKind, str] = {
    FrameKind.THERMODYNAMIC: "Frame: thermodynamic",
    FrameKind.INFORMATION_THEORETIC: "Frame: information-theoretic",
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY:
        "Frame: ontological distinguishability",
    FrameKind.METAPHORICAL: "Frame: metaphorical",
    FrameKind.FORMAL_LOGIC: "Frame: formal logic",
    FrameKind.EMPIRICAL_CAUSAL: "Frame: empirical causal",
    FrameKind.AUTHORITY_SPEECH: "Frame: authority",
    FrameKind.TOOL_COMPUTABLE: "Frame: tool computable",
    FrameKind.FRAME_UNDECLARED: "Frame: undeclared",
}


# Prior-sentence fixtures per frame — deterministic, no LLM.
_FIXTURE_PRIOR: dict[FrameKind, str] = {
    FrameKind.THERMODYNAMIC:
        "We measure heat flow in joules per second.",
    FrameKind.INFORMATION_THEORETIC:
        "Channel capacity is measured in bits per use.",
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY:
        "Identity statements concern referential sameness.",
    FrameKind.METAPHORICAL:
        "We will speak loosely in the next paragraph.",
    FrameKind.FORMAL_LOGIC:
        "All inferences obey modus ponens here.",
    FrameKind.EMPIRICAL_CAUSAL:
        "We catalogue observed cause-effect chains.",
    FrameKind.AUTHORITY_SPEECH:
        "The following report is a third-party statement.",
    FrameKind.TOOL_COMPUTABLE:
        "The following question expects a numerical answer.",
    FrameKind.FRAME_UNDECLARED:
        "Context for the following claim is unspecified.",
}


@dataclass(frozen=True)
class TargetCase:
    """One entropy-bearing target case with context window."""

    case_id: str
    text: str
    expected_frame: FrameKind
    detected_frame: FrameKind | None    # what v3.4 detector said, or None
    source_benchmark: str
    context_window: ContextWindow

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
            "detected_frame": (
                self.detected_frame.value if self.detected_frame else None
            ),
            "source_benchmark": self.source_benchmark,
            "context_window": self.context_window.to_dict(),
        }


def _build_window(text: str, expected_frame: FrameKind) -> ContextWindow:
    return ContextWindow(
        ctx_0=text,
        ctx_1=_FIXTURE_PRIOR[expected_frame],
        ctx_2=_FIXTURE_HEADER[expected_frame],
        ctx_3=_FIXTURE_DOC_FRAME[expected_frame],
    )


def extract_entropy_targets() -> tuple[TargetCase, ...]:
    """Aufgabe 1 — every entropy-bearing case from v3.4 / v3.5 / v3.6."""
    out: list[TargetCase] = []

    # v3.4 frame benchmark: entropy-bearing cases.
    for c in ALL_FRAME_CASES:
        if "entropy" not in c.text.lower():
            continue
        out.append(TargetCase(
            case_id=f"v34:{c.case_id}",
            text=c.text,
            expected_frame=c.expected_frame,
            detected_frame=None,
            source_benchmark="v3.4 frame benchmark",
            context_window=_build_window(c.text, c.expected_frame),
        ))

    # v3.5 invariance — info-theoretic paraphrases that literally
    # mention "entropy" (other paraphrases use mutual-information /
    # bits / Shannon vocabulary and are not entropy-polysemy cases).
    for g in INV_GROUPS:
        if g.expected_frame is not FrameKind.INFORMATION_THEORETIC:
            continue
        for idx, text in enumerate(g.all_texts()):
            if "entropy" not in text.lower():
                continue
            out.append(TargetCase(
                case_id=f"v35:{g.group_id}:p{idx}",
                text=text,
                expected_frame=g.expected_frame,
                detected_frame=None,
                source_benchmark="v3.5 invariance",
                context_window=_build_window(text, g.expected_frame),
            ))

    # v3.5 invariance negative-controls — both halves of any pair
    # whose text mentions entropy.
    for nc in INV_NCS:
        for label, text, frame in (
            ("a", nc.text_a, nc.frame_a),
            ("b", nc.text_b, nc.frame_b),
        ):
            if "entropy" not in text.lower():
                continue
            out.append(TargetCase(
                case_id=f"v35-nc:{nc.nc_id}.{label}",
                text=text,
                expected_frame=frame,
                detected_frame=None,
                source_benchmark="v3.5 invariance NC",
                context_window=_build_window(text, frame),
            ))

    # v3.6 failure-audit negative-controls with entropy.
    for nc in FA_NCS:
        if "entropy" not in nc.text.lower():
            continue
        out.append(TargetCase(
            case_id=f"v36-nc:{nc.nc_id}",
            text=nc.text,
            expected_frame=nc.expected_frame,
            detected_frame=None,
            source_benchmark="v3.6 failure-audit NC",
            context_window=_build_window(nc.text, nc.expected_frame),
        ))

    # v3.6 actual failure records — every entropy-bearing failure
    # carries the detector's wrong verdict, which is exactly the
    # baseline this probe needs to compare context-inheritance
    # against. Texts may duplicate v3.5 paraphrases above; we keep
    # both because the v3.6 lens adds the detector's verdict.
    _now = datetime.now(timezone.utc)
    audit = build_audit_report(started_at=_now, finished_at=_now)
    for f in audit.failures:
        if "entropy" not in f.text.lower():
            continue
        out.append(TargetCase(
            case_id=f"v36-fail:{f.case_id}",
            text=f.text,
            expected_frame=f.expected_frame,
            detected_frame=f.detected_frame,
            source_benchmark="v3.6 failure-audit",
            context_window=_build_window(f.text, f.expected_frame),
        ))

    return tuple(out)


__all__ = [
    "ContextWindow",
    "TargetCase",
    "extract_entropy_targets",
]
