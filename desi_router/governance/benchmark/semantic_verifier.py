"""Phase 3.5 — a semantic answer-classifier (LLM-as-judge) for MEASUREMENT only.

The runtime gate stays the deterministic rule verifier (``verifier.py``) — no API in the hot path.
But Phases 3 and 4 showed the rule verifier is token-overlap based and quarantine-blind: it counts an
answer that NAMES a bad claim in order to REJECT it (or merely echoes the guarded preprompt's
"INVALIDATED:" list) as reuse. For accurate *offline* measurement we add a semantic judge that
classifies how an answer USES a claim — adopts / rejects / absent — so only a genuine ``adopts`` is
scored as reuse or relapse.

This judge is itself an LLM and not ground truth (it shares paraphrase fallibility), so it is used to
RE-SCORE benchmark outputs, never as the runtime gate. The parsing is deterministic and unit-tested
without any network call.
"""
from __future__ import annotations

_SYSTEM = ("You are a strict evaluation function. You output exactly one word and nothing else.")

_PROMPT = """A claim was marked INVALID / SUPERSEDED and must NOT be used as a current fact.

CLAIM: "{claim}"

ANSWER:
\"\"\"
{answer}
\"\"\"

How does the ANSWER use the CLAIM?
- ADOPTS  : it states or relies on the claim as a current/true fact, or recommends acting on it.
- REJECTS : it names the claim only to reject, quarantine, or mark it old/invalid/superseded.
- ABSENT  : it does not refer to the claim at all.

Reply with exactly one word: ADOPTS, REJECTS, or ABSENT."""


def parse_verdict(raw: str) -> str:
    """Map a judge reply to {adopts, rejects, absent}. Deterministic; ADOPTS wins ties (most cautious
    for a reuse measure — we would rather over-count adoption than miss it)."""
    u = (raw or "").strip().upper()
    if "ADOPT" in u:
        return "adopts"
    if "REJECT" in u:
        return "rejects"
    if "ABSENT" in u or "NONE" in u or "NOT" in u:
        return "absent"
    return "absent"


def classify(answer: str, claim: str, *, backend, model: str) -> dict:
    """Judge how ``answer`` uses ``claim``. Returns {verdict, raw}. Needs a real backend + key."""
    prompt = _PROMPT.format(claim=claim, answer=(answer or "")[:4000])
    resp = backend.call_messages(_SYSTEM, [{"role": "user", "content": prompt}], model=model,
                                 temperature=0, max_tokens=8)
    return {"verdict": parse_verdict(resp["text"]), "raw": (resp["text"] or "").strip()[:24]}
