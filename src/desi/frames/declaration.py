"""FrameDeclaration — Aufgabe 2.

Pure data record. Produced by :class:`FrameDetector`. Carries a
deterministic ``replay_hash`` so two declarations on the same
input text produce byte-identical records (modulo
``frame_id`` / ``claim_id`` if those are derived externally).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .kinds import DetectionMethod, FrameKind


@dataclass(frozen=True)
class FrameDeclaration:
    frame_id: str
    claim_id: str
    frame_kind: FrameKind
    source_text: str
    detection_method: DetectionMethod
    confidence: float
    rationale: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "claim_id": self.claim_id,
            "frame_kind": self.frame_kind.value,
            "source_text": self.source_text,
            "detection_method": self.detection_method.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "replay_hash": self.replay_hash,
        }


def make_frame_id(source_text: str, frame_kind: FrameKind) -> str:
    raw = f"{frame_kind.value}|{source_text.strip().lower()}"
    return "fr_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def compute_frame_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items() if k != "replay_hash"}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "FrameDeclaration",
    "compute_frame_replay_hash",
    "make_frame_id",
]
