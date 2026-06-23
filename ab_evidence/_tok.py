"""Offline token estimate for the ablation harness.

Prefers the project's canonical tokenizer (``claude_compression/state.py`` — the same
``token_count`` the existing A/B harness uses). When that module is not checked out (it is an
optional sibling package), falls back to a deterministic, tokenizer-free word/punctuation count so
the ablation harness still runs. The fallback is APPROXIMATE and is used only for *relative* budget
comparison across conditions; it never regenerates the canonical results files.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_CC = Path(__file__).resolve().parents[1] / "claude_compression"


def _load_canonical():
    if _CC.exists():
        sys.path.insert(0, str(_CC))
        try:
            from state import token_count as _tc  # type: ignore  # noqa: E402
            return _tc
        except Exception:  # noqa: BLE001 - absent/broken sibling pkg -> use the fallback
            return None
    return None


_canonical = _load_canonical()
IS_FALLBACK = _canonical is None


def _fallback(text: str) -> int:
    # deterministic, dependency-free: count word-ish runs and standalone punctuation. This tracks
    # real subword token counts closely enough for the only thing it is used for here: comparing
    # the budget of one condition against another.
    if not text:
        return 0
    return len(re.findall(r"\w+|[^\w\s]", text))


def token_count(text: str) -> int:
    if _canonical is not None:
        return _canonical(text or "")
    return _fallback(text or "")
