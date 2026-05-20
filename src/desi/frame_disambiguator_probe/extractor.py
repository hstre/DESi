"""Target + counter-set extraction — Aufgaben 1 + 3."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_failure_audit import (
    NEGATIVE_CONTROLS as FA_NEGATIVE_CONTROLS,
    extract_failures,
)
from ..frame_invariance import (
    NEGATIVE_CONTROLS as INV_NEGATIVE_CONTROLS,
)
from ..frames import FrameKind


_TOKEN_RE = re.compile(r"[a-z][a-z0-9-]+")


@dataclass(frozen=True)
class TargetCase:
    case_id: str
    text: str
    expected_frame: FrameKind
    detected_frame: FrameKind
    tokens: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
            "detected_frame": self.detected_frame.value,
            "tokens": list(self.tokens),
        }


@dataclass(frozen=True)
class CounterCase:
    """One entropy-bearing case that a patch must NOT absorb."""

    source: str            # "v3.4:FA_01", "v3.5:NC", "v3.6:NC"
    text: str
    expected_frame: FrameKind   # the *not-info-theoretic* frame

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
        }


def _content_tokens(text: str) -> tuple[str, ...]:
    """Lowercase tokens >= 3 chars, deduped, sorted for determinism."""
    return tuple(sorted({
        m.group(0) for m in _TOKEN_RE.finditer(text.lower())
        if len(m.group(0)) >= 3
    }))


def extract_polysemy_targets() -> tuple[TargetCase, ...]:
    """Aufgabe 1 — pull the 15 polysemy-collision /
    information-theoretic failures from v3.5 (re-run via the
    failure-audit extractor)."""
    targets: list[TargetCase] = []
    for f in extract_failures():
        if (
            f.expected_frame is not FrameKind.INFORMATION_THEORETIC
            or "entropy" not in f.text.lower()
        ):
            continue
        targets.append(TargetCase(
            case_id=f.case_id,
            text=f.text,
            expected_frame=f.expected_frame,
            detected_frame=f.detected_frame,
            tokens=_content_tokens(f.text),
        ))
    return tuple(targets)


def extract_thermo_counter_set() -> tuple[CounterCase, ...]:
    """Aufgabe 3 — entropy-bearing cases that are NOT
    information-theoretic. Collected from:

    * v3.4 frame benchmark (FA_01, FH_01, FH_04)
    * v3.5 invariance negative-controls (N01.a)
    * v3.6 failure-audit negative-controls (NC01, NC02)
    """
    out: list[CounterCase] = []
    for c in ALL_FRAME_CASES:
        if "entropy" not in c.text.lower():
            continue
        if c.expected_frame is FrameKind.INFORMATION_THEORETIC:
            continue
        out.append(CounterCase(
            source=f"v3.4:{c.case_id}",
            text=c.text, expected_frame=c.expected_frame,
        ))
    for nc in INV_NEGATIVE_CONTROLS:
        for label, text, frame in (
            ("a", nc.text_a, nc.frame_a),
            ("b", nc.text_b, nc.frame_b),
        ):
            if "entropy" not in text.lower():
                continue
            if frame is FrameKind.INFORMATION_THEORETIC:
                continue
            out.append(CounterCase(
                source=f"v3.5-inv:{nc.nc_id}.{label}",
                text=text, expected_frame=frame,
            ))
    for nc in FA_NEGATIVE_CONTROLS:
        if "entropy" not in nc.text.lower():
            continue
        if nc.expected_frame is FrameKind.INFORMATION_THEORETIC:
            continue
        out.append(CounterCase(
            source=f"v3.6-fa:{nc.nc_id}",
            text=nc.text, expected_frame=nc.expected_frame,
        ))
    return tuple(out)


__all__ = [
    "CounterCase",
    "TargetCase",
    "extract_polysemy_targets",
    "extract_thermo_counter_set",
]
