"""Aufgabe 3 — assemble the simulation corpus.

Pulls cases from four upstream sources:

* v3.8 false-inheritance fixtures — misleading outer context
* v3.9 manipulation set — adversarial inner/outer mismatches
* v3.10 tension audit — every v3.9 FRAME_TENSION case + verdict
* v3.11 runtime benchmark — 40 layer cases (10 per FrameConsistency)

The directive requires ≥ 80 cases total and ≥ 20 adversarial.
Each case carries a closed ``CorpusOrigin`` tag and an
``is_adversarial`` flag.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from ..frame_consistency_probe.manipulation import MANIPULATIONS
from ..frame_context_probe.false_inheritance import NEGATIVE_CONTROLS
from ..frame_tension import ALL_LAYER_CASES, FrameConsistency
from .enums import CorpusOrigin


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V310_REPORT = _REPO_ROOT / "artifacts" / "v3_10" / "report.json"


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    claim_text: str
    inherited_context_text: str
    expected_consistency: FrameConsistency | None
    is_adversarial: bool
    origin: CorpusOrigin

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "claim_text": self.claim_text,
            "inherited_context_text": self.inherited_context_text,
            "expected_consistency": (
                self.expected_consistency.value
                if self.expected_consistency else None
            ),
            "is_adversarial": self.is_adversarial,
            "origin": self.origin.value,
        }


def _from_v311_benchmark() -> tuple[CorpusCase, ...]:
    out: list[CorpusCase] = []
    for c in ALL_LAYER_CASES:
        out.append(CorpusCase(
            case_id=f"v311:{c.case_id}",
            claim_text=c.claim_text,
            inherited_context_text=c.inherited_context_text,
            expected_consistency=c.expected,
            # The 10 CONFIRMED + 10 UNDECIDABLE cases are benign;
            # the 10 TENSION + 10 CONFLICT cases are by construction
            # adversarial-shaped (inner ≠ outer).
            is_adversarial=c.expected in (
                FrameConsistency.TENSION,
                FrameConsistency.CONFLICT,
            ),
            origin=CorpusOrigin.V311_RUNTIME,
        ))
    return tuple(out)


def _from_v39_manipulations() -> tuple[CorpusCase, ...]:
    out: list[CorpusCase] = []
    for m in MANIPULATIONS:
        # Every manipulation is adversarial by construction;
        # expected consistency is not-CONFIRMED (the layer must
        # not silently allow the inherited outer).
        out.append(CorpusCase(
            case_id=f"v39manip:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
            expected_consistency=None,  # "must-not-allow", any block ok
            is_adversarial=True,
            origin=CorpusOrigin.V39_MANIPULATION,
        ))
    return tuple(out)


def _from_v38_inheritance() -> tuple[CorpusCase, ...]:
    out: list[CorpusCase] = []
    for nc in NEGATIVE_CONTROLS:
        # The misleading window is the v3.8 fixture; we attach
        # its ctx_3 as the inherited context the runtime layer
        # would see in production.
        out.append(CorpusCase(
            case_id=f"v38fn:{nc.case_id}",
            claim_text=nc.text,
            inherited_context_text=nc.misleading_window.ctx_3,
            expected_consistency=None,
            is_adversarial=True,
            origin=CorpusOrigin.V38_INHERITANCE,
        ))
    return tuple(out)


def _from_v310_audit() -> tuple[CorpusCase, ...]:
    if not _V310_REPORT.exists():
        return ()
    data = json.loads(_V310_REPORT.read_text(encoding="utf-8"))
    out: list[CorpusCase] = []
    for o in data["outcomes"]:
        tgt = o["target"]
        # The v3.10 audit's TENSION cases were classified as
        # TRUE_TENSION (real) vs FALSE/AMBIGUOUS. For corpus
        # purposes we mark TRUE_TENSION as adversarial-shaped.
        adversarial = o["audit_class"] == "true_tension"
        out.append(CorpusCase(
            case_id=f"v310:{tgt['case_id']}",
            claim_text=tgt["text"],
            # The v3.10 audit does not carry the full 4-layer
            # context window — only the outer frame. We
            # reconstruct a minimal outer context using the
            # explicit Frame marker so the runtime layer sees
            # the same outer signal it would in production.
            inherited_context_text=(
                f"Frame: {tgt['outer_frame']}" if tgt['outer_frame']
                else ""
            ),
            expected_consistency=FrameConsistency.TENSION,
            is_adversarial=adversarial,
            origin=CorpusOrigin.V310_TENSION_AUDIT,
        ))
    return tuple(out)


def build_corpus() -> tuple[CorpusCase, ...]:
    cases = (
        _from_v311_benchmark()
        + _from_v39_manipulations()
        + _from_v38_inheritance()
        + _from_v310_audit()
    )
    if len(cases) < 80:
        raise RuntimeError(
            f"corpus has {len(cases)} cases, need >= 80"
        )
    adversarial = sum(1 for c in cases if c.is_adversarial)
    if adversarial < 20:
        raise RuntimeError(
            f"corpus has {adversarial} adversarial cases, need >= 20"
        )
    return cases


def corpus_summary() -> dict[str, Any]:
    cases = build_corpus()
    by_origin: dict[str, int] = {}
    for c in cases:
        by_origin[c.origin.value] = by_origin.get(c.origin.value, 0) + 1
    return {
        "total": len(cases),
        "adversarial": sum(1 for c in cases if c.is_adversarial),
        "by_origin": dict(sorted(by_origin.items())),
    }


__all__ = [
    "CorpusCase",
    "build_corpus",
    "corpus_summary",
]
