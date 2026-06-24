"""Automatic DESi state construction — the Phase-4 test of the Phase-3 caveat.

Phase 3 showed a CURATED DESi state beats retrieval on lifecycle cases, but B's slice was the
human-authored ground-truth live state. The open question: can that state be BUILT automatically?

Here one LLM extraction pass reads the raw chat and emits the current live state as categorised JSON,
explicitly told to drop anything later reversed / ruled out / deprecated / superseded (LLM for
language; the downstream summary task is unchanged). ``B_auto`` then runs on this constructed slice.

  If B_auto ≈ B (curated) and still beats retrieval → auto-construction works on these cases.
  If B_auto ≈ retrieval → the value was the human curation, not constructible (yet).

The extractor reads ONLY the chat (never the ground truth), so this is a fair test.
"""
from __future__ import annotations

import json

import backend
from build_state import load_chat

_CATS = ("active_claims", "active_constraints", "decisions", "open_conflicts", "open_questions")

_SYS = (
    "You extract the CURRENT live state of a working conversation. Output ONLY a JSON object with "
    "keys active_claims, active_constraints, decisions, open_conflicts, open_questions; each a list "
    "of objects {\"id\": ..., \"what\": ...}. CRITICAL: if a decision, claim, or constraint was "
    "later reversed, ruled out, deprecated, or superseded in the conversation, record ONLY what "
    "holds NOW — never the superseded version. Be concise; no commentary outside the JSON."
)


def _parse(text: str) -> dict:
    s, e = text.find("{"), text.rfind("}")
    obj = {}
    if s >= 0 and e > s:
        try:
            obj = json.loads(text[s:e + 1])
        except Exception:  # noqa: BLE001 - malformed extraction -> empty state (a fair failure)
            obj = {}
    out: dict = {}
    for cat in _CATS:
        items = obj.get(cat) if isinstance(obj, dict) else None
        norm = []
        for j, it in enumerate(items if isinstance(items, list) else []):
            if isinstance(it, dict) and str(it.get("what", "")).strip():
                norm.append({"id": str(it.get("id") or f"{cat[0].upper()}{j + 1}"),
                             "what": str(it["what"]).strip()})
            elif isinstance(it, str) and it.strip():
                norm.append({"id": f"{cat[0].upper()}{j + 1}", "what": it.strip()})
        out[cat] = norm
    return out


def construct_state(case_id: str, *, model=None, temperature: float = 0.0, seed: int = 0) -> dict:
    """One extraction pass over the raw chat → categorised current-live-state dict (B's shape)."""
    convo = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in load_chat(case_id))
    resp = backend.call_messages(
        _SYS, [{"role": "user", "content": f"CONVERSATION:\n{convo}\n\nExtract the current live "
                "state as JSON."}],
        model=model, temperature=temperature, seed=seed, max_tokens=1024)
    return _parse(resp.get("text", ""))
