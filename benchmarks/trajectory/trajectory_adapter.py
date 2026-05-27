"""Trajectory adapter for DriftBench (PERIPHERAL, deterministic, no LLM).

Turns a DriftBench item (brief + multi-turn transcript) into a per-turn trajectory
of DESi-relevant signals, computed deterministically from text:
  * constraint_retention  -- mean lexical coverage of the brief's hard_constraints
  * banned_incursion      -- how many banned_moves surface in the turn
  * objective_overlap     -- lexical coverage of the brief objective
  * alternative_coverage  -- how many plausible_directions are still in play
  * desi_frame            -- the DESi-core FrameDetector frame for the turn
                             (read-only projection through the existing semantic
                             layer; used for a frame_flip drift signal)

No model calls, no gold-label use, no DESi-core change. The DESi frame layer is
imported read-only to provide the "DESi analyses the trajectory" projection.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "are", "was",
    "were", "be", "been", "being", "that", "this", "these", "those", "it", "its",
    "as", "at", "by", "for", "with", "from", "has", "have", "had", "do", "does",
    "did", "but", "if", "then", "than", "so", "such", "into", "out", "up", "down",
    "over", "under", "about", "their", "they", "them", "we", "you", "i", "which",
    "who", "must", "no", "not", "only", "any", "all", "per", "use", "using",
))


def _content(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (text or "").lower()) if t not in _STOP and len(t) > 2}


def coverage(needle: str, haystack: str) -> float:
    """Fraction of `needle`'s content tokens present in `haystack` (deterministic)."""
    nt = _content(needle)
    if not nt:
        return 0.0
    ht = _content(haystack)
    return round(len(nt & ht) / len(nt), 3)


def _hit(phrase: str, text: str, thresh: float = 0.6) -> bool:
    return coverage(phrase, text) >= thresh


_FRAME_DETECTOR = None


def _frame(text: str) -> str:
    global _FRAME_DETECTOR
    try:
        if _FRAME_DETECTOR is None:
            from desi.frames import FrameDetector
            _FRAME_DETECTOR = FrameDetector()
        return _FRAME_DETECTOR.detect(claim_id="traj", source_text=text[:4000]).frame_kind.value
    except Exception:
        return "unavailable"


def assistant_turns(item: dict) -> list:
    return [m["content"] for m in item.get("messages", []) if m.get("role") == "assistant"]


def to_trajectory(item: dict) -> list:
    """Per-assistant-turn deterministic DESi-relevant signals."""
    brief = item.get("brief", {})
    constraints = brief.get("hard_constraints", []) or []
    banned = brief.get("banned_moves", []) or []
    directions = brief.get("plausible_directions", []) or []
    objective = brief.get("objective", "") or ""
    turns = assistant_turns(item)
    out = []
    for i, text in enumerate(turns):
        cret = [coverage(c, text) for c in constraints]
        out.append({
            "turn": i,
            "constraint_retention": round(sum(cret) / len(cret), 3) if cret else 0.0,
            "banned_incursion": sum(1 for b in banned if _hit(b, text)),
            "objective_overlap": coverage(objective, text),
            "alternative_coverage": sum(1 for d in directions if _hit(d, text)),
            "desi_frame": _frame(text),
        })
    return out


__all__ = ["assistant_turns", "coverage", "to_trajectory"]
