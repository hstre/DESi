"""FrameDetector — Aufgabe 3.

Three-tier detection, evaluated in strict order:

1. **Explicit marker** — ``Frame: <name>`` substring (case-insensitive),
   matched against the closed set of canonical labels.
2. **Rule-based** — substring patterns on the lower-cased source
   text, mapped into closed marker buckets. **Multiple buckets
   may match**; the caller (and the compatibility checker) decides
   what to do when more than one fires.
3. **Default undeclared** — no marker and no bucket: emit
   ``FrameKind.FRAME_UNDECLARED`` with
   ``DetectionMethod.DEFAULT_UNDECLARED``.

The detector never calls an LLM, never authoritative-promotes,
never decides truth. It picks **which pipeline** the claim may
even enter.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .declaration import (
    FrameDeclaration,
    compute_frame_replay_hash,
    make_frame_id,
)
from .kinds import DetectionMethod, FrameKind


# Marker → canonical FrameKind. Case-insensitive substring match
# on a ``Frame:`` prefix.
_EXPLICIT_MARKERS: tuple[tuple[str, FrameKind], ...] = (
    ("frame: thermodynamic", FrameKind.THERMODYNAMIC),
    ("frame: information-theoretic", FrameKind.INFORMATION_THEORETIC),
    ("frame: information theoretic", FrameKind.INFORMATION_THEORETIC),
    ("frame: ontological distinguishability",
     FrameKind.ONTOLOGICAL_DISTINGUISHABILITY),
    ("frame: metaphorical", FrameKind.METAPHORICAL),
    ("frame: formal logic", FrameKind.FORMAL_LOGIC),
    ("frame: empirical causal", FrameKind.EMPIRICAL_CAUSAL),
    ("frame: authority", FrameKind.AUTHORITY_SPEECH),
    ("frame: tool computable", FrameKind.TOOL_COMPUTABLE),
    ("frame: undeclared", FrameKind.FRAME_UNDECLARED),
)


# Rule-based buckets. Each key carries a closed list of substrings
# (lower-cased, leading-space-padded to avoid sub-word matches when
# possible).
_RULE_BUCKETS: tuple[tuple[FrameKind, tuple[str, ...]], ...] = (
    (FrameKind.THERMODYNAMIC, (
        "entropy", "heat ", "temperature", "thermodynamic",
        "joule", "kelvin",
    )),
    (FrameKind.INFORMATION_THEORETIC, (
        # ``entropy`` is intentionally listed here too — it is the
        # canonical example of a term that, without an explicit
        # frame marker, fires both thermodynamic and information-
        # theoretic buckets simultaneously and so triggers
        # FRAME_CONFLICT.
        "entropy", "bits", "shannon", "mutual information",
        "kolmogorov", "information-theoretic",
        "information theoretic", "channel capacity",
    )),
    (FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, (
        "same object", "distinguishable", "indistinguishable",
        "identity of", "ontological", "numerically identical",
    )),
    (FrameKind.METAPHORICAL, (
        "like a", "as if", "metaphorically", "in a sense",
        "loosely speaking", "figuratively",
    )),
    (FrameKind.FORMAL_LOGIC, (
        "all a are b", "all a are c", "therefore",
        "every x is", "modus ponens", "syllogism",
    )),
    (FrameKind.EMPIRICAL_CAUSAL, (
        " causes ", " caused ", "leads to", "led to",
        "because of", "results in", "resulted in", "due to",
    )),
    (FrameKind.AUTHORITY_SPEECH, (
        " says ", " said ", " states ", " stated ",
        " claims ", " claimed ", " declares ", " declared ",
        " announces ", " announced ", " publishes ", " published ",
        " proves ", " proved ", " reports ", " reported ",
        " concludes ", " concluded ", "according to ",
    )),
    (FrameKind.TOOL_COMPUTABLE, (
        " + ", " - ", " * ", " / ", " = ",
        "how many", "what is the sum", "how many days",
        "compute ", "calculate ",
    )),
)


@dataclass(frozen=True)
class DetectionResult:
    """Internal — what the detector finds before reconciliation."""

    explicit_kind: FrameKind | None
    rule_kinds: tuple[FrameKind, ...]


def _explicit_marker(text: str) -> FrameKind | None:
    low = text.lower()
    for marker, kind in _EXPLICIT_MARKERS:
        if marker in low:
            return kind
    return None


def _rule_buckets(text: str) -> tuple[FrameKind, ...]:
    padded = " " + text.lower() + " "
    fired: list[FrameKind] = []
    for kind, markers in _RULE_BUCKETS:
        for m in markers:
            if m in padded:
                fired.append(kind)
                break
    return tuple(fired)


class FrameDetector:
    """Pure, deterministic frame detection. No LLM, no network."""

    def detect(
        self,
        *,
        claim_id: str,
        source_text: str,
    ) -> FrameDeclaration:
        explicit = _explicit_marker(source_text)
        if explicit is not None:
            return self._declare(
                claim_id=claim_id,
                source_text=source_text,
                frame_kind=explicit,
                detection_method=DetectionMethod.EXPLICIT_MARKER,
                confidence=1.0,
                rationale=f"explicit marker matched: {explicit.value}",
                rule_kinds=(explicit,),
            )

        buckets = _rule_buckets(source_text)
        if not buckets:
            return self._declare(
                claim_id=claim_id,
                source_text=source_text,
                frame_kind=FrameKind.FRAME_UNDECLARED,
                detection_method=DetectionMethod.DEFAULT_UNDECLARED,
                confidence=0.0,
                rationale="no marker, no rule bucket matched",
                rule_kinds=(),
            )

        # Exactly one bucket fired — that's the declared frame.
        unique = tuple(dict.fromkeys(buckets))  # preserves order, dedupes
        if len(unique) == 1:
            return self._declare(
                claim_id=claim_id,
                source_text=source_text,
                frame_kind=unique[0],
                detection_method=DetectionMethod.RULE_BASED,
                confidence=0.8,
                rationale=f"rule bucket: {unique[0].value}",
                rule_kinds=unique,
            )

        # Multiple incompatible buckets fired — frame conflict.
        return self._declare(
            claim_id=claim_id,
            source_text=source_text,
            frame_kind=FrameKind.FRAME_UNDECLARED,
            detection_method=DetectionMethod.RULE_BASED,
            confidence=0.0,
            rationale=(
                "frame conflict: multiple buckets fired "
                f"({', '.join(k.value for k in unique)})"
            ),
            rule_kinds=unique,
        )

    @staticmethod
    def _declare(
        *,
        claim_id: str,
        source_text: str,
        frame_kind: FrameKind,
        detection_method: DetectionMethod,
        confidence: float,
        rationale: str,
        rule_kinds: tuple[FrameKind, ...],
    ) -> FrameDeclaration:
        payload = {
            "claim_id": claim_id,
            "frame_kind": frame_kind.value,
            "source_text": source_text,
            "detection_method": detection_method.value,
            "confidence": confidence,
            "rationale": rationale,
            "rule_kinds": [k.value for k in rule_kinds],
        }
        replay_hash = compute_frame_replay_hash(payload)
        return FrameDeclaration(
            frame_id=make_frame_id(source_text, frame_kind),
            claim_id=claim_id,
            frame_kind=frame_kind,
            source_text=source_text,
            detection_method=detection_method,
            confidence=confidence,
            rationale=rationale,
            replay_hash=replay_hash,
        )

    def detect_conflicting_buckets(
        self, source_text: str,
    ) -> tuple[FrameKind, ...]:
        """Public helper for Aufgabe 6 — return every bucket that
        fired, deduplicated, in detection order. The compatibility
        layer uses this to surface ``FrameKind.FRAME_UNDECLARED``
        with a ``frame conflict`` rationale.
        """
        explicit = _explicit_marker(source_text)
        if explicit is not None:
            return (explicit,)
        return tuple(dict.fromkeys(_rule_buckets(source_text)))


__all__ = ["DetectionResult", "FrameDetector"]
