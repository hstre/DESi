"""Falsification-oriented ablation conditions for the DESi state-injection A/B harness.

Four conditions over the SAME case and the SAME follow-up task:

  A_baseline_full_context — the full chat history (mirrors variant A of the original harness).
  B_normal_desi           — the case's own categorised DESi state slice (mirrors variant B).
  C_wrong_slice           — B's exact FORMAT and approximate budget, but the slice is ANOTHER
                            case's state (a plausible-but-incorrect DESi slice). If the model does
                            about as well here as on B, the gain is mostly generic structured
                            context, not correct slice selection.
  D_status_stripped       — the SAME selected claim TEXTS as B, with the epistemic-governance
                            metadata removed: the category typing (active_claims / constraints /
                            decisions / open_conflicts / open_questions = role + lifecycle +
                            admissibility), the typed IDs (C/R/D/K/Q…), and any evidence / claim_ids
                            fields. The claims become an undifferentiated, same-order bag of
                            sentences. If D ≈ B, DESi here is mostly context selection; if B > D
                            (esp. on conflict/decision typing and on degeneration), the governance
                            metadata is carrying value.

A and B are re-declared here rather than imported from ``prompts.py`` because that module imports the
optional ``claude_compression`` tokenizer at load time; the system strings below are copied verbatim
from it so the A/B conditions stay identical to the canonical harness.
"""
from __future__ import annotations

import json

from _tok import token_count
from build_state import load_chat, state_for_variant_B
from follow_up_tasks import FOLLOW_UPS

# --- verbatim from prompts.py (kept in sync; A/B must match the canonical harness) ---------------
_SYSTEM_BASE = (
    "You are continuing prior work. Answer the user's question using ONLY the context you have. "
    "Do not invent facts. If a category has no entries, write 'none'."
)
_SYSTEM_B_EXTRA = (
    " The original chat is NOT included. Below the question is a structured DESi state with the "
    "active claims, constraints, decisions, open conflicts, and open questions."
)
# For D the categories are GONE, so the system must not name them. It is the same epistemic framing
# (continue from carried-over context) minus the typed-state description — nothing is added.
_SYSTEM_D_EXTRA = (
    " The original chat is NOT included. Below the question is a list of notes carried over from the "
    "prior work."
)

CONDITIONS = ("A_baseline_full_context", "B_normal_desi", "C_wrong_slice", "D_status_stripped",
              "E_budget_matched_status_stripped")

# Deterministic donor for the wrong slice: a DIFFERENT-domain case with a real, structurally valid
# state. Long-research cases borrow a non-long-research donor so the mismatch is unambiguous.
WRONG_SLICE_DONOR = {
    "case1_architecture": "case3_debugging",
    "case2_research": "case1_architecture",
    "case3_debugging": "case2_research",
    "case4_long_research": "case3_debugging",
    "case5_long_research": "case2_research",
    "case6_long_research": "case3_debugging",
    "case7a_padded_30k": "case2_research",
    "case7b_padded_60k": "case2_research",
}

_STATE_ORDER = ("active_claims", "active_constraints", "decisions", "open_conflicts",
                "open_questions")


def _state_block(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _user_with_context(follow_up: str, block: str, label: str) -> str:
    return f"{follow_up}\n\n---\n{label}:\n{block}\n---"


def status_strip(state: dict) -> list[str]:
    """Remove ALL epistemic-governance metadata, keep only the claim texts in their original order.

    Dropped: the five category buckets (role / lifecycle / admissibility), the typed IDs, and any
    ``evidence`` / ``claim_ids`` fields. Kept: the ``what`` body of every entry, in the canonical
    category order, so ordering and wording are comparable to B. Returns a flat list of strings.
    """
    flat: list[str] = []
    for cat in _STATE_ORDER:
        for item in state.get(cat, []):
            flat.append(item["what"])
    return flat


def _messages_A(case_id: str) -> dict:
    chat = load_chat(case_id)
    messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in chat]
    messages.append({"role": "user", "content": FOLLOW_UPS[case_id]})
    return {"condition": "A_baseline_full_context", "system": _SYSTEM_BASE,
            "messages": messages, "slice_source": None}


def _b_user(case_id: str) -> str:
    return _user_with_context(FOLLOW_UPS[case_id], _state_block(state_for_variant_B(case_id)),
                              "DESi state")


def _messages_B(case_id: str) -> dict:
    return {"condition": "B_normal_desi", "system": _SYSTEM_BASE + _SYSTEM_B_EXTRA,
            "messages": [{"role": "user", "content": _b_user(case_id)}], "slice_source": case_id}


def _messages_C(case_id: str) -> dict:
    donor = WRONG_SLICE_DONOR[case_id]
    state = state_for_variant_B(donor)   # another case's state — identical FORMAT, wrong content
    user = _user_with_context(FOLLOW_UPS[case_id], _state_block(state), "DESi state")
    return {"condition": "C_wrong_slice", "system": _SYSTEM_BASE + _SYSTEM_B_EXTRA,
            "messages": [{"role": "user", "content": user}], "slice_source": donor}


def _messages_D(case_id: str) -> dict:
    notes = status_strip(state_for_variant_B(case_id))
    block = json.dumps(notes, ensure_ascii=False)   # flat list: no keys, no ids, no categories
    user = _user_with_context(FOLLOW_UPS[case_id], block, "Notes")
    return {"condition": "D_status_stripped", "system": _SYSTEM_BASE + _SYSTEM_D_EXTRA,
            "messages": [{"role": "user", "content": user}], "slice_source": case_id}


def _messages_E(case_id: str) -> dict:
    """Budget-matched status-stripped: D's exact claim texts, no governance metadata, padded to B's
    token budget with INERT filler so a B>D gap cannot be dismissed as 'B just had more tokens'.

    The notes are wrapped with neutral, meaning-free keys (``items``/``ref``/``note``) — ``ref`` is
    pure 1-based ordering, NOT a typed governance id (C/R/D/K/Q) — and the remaining gap to B's
    budget is filled with a single ``_padding`` field of repeated single-char tokens. The filler has
    no content tokens (``len > 2`` are filtered by the evaluator's tokeniser), so it can neither
    match ground truth nor leak epistemic information. No categories, validity, evidence or
    provenance are present: same information as D, same budget as B.
    """
    notes = status_strip(state_for_variant_B(case_id))
    obj: dict = {"items": [{"ref": f"i{i + 1}", "note": n} for i, n in enumerate(notes)]}
    system = _SYSTEM_BASE + _SYSTEM_D_EXTRA

    def _user_for(o: dict) -> str:
        return _user_with_context(FOLLOW_UPS[case_id], _state_block(o), "Notes")

    target = token_count(_SYSTEM_BASE + _SYSTEM_B_EXTRA) + token_count(_b_user(case_id))
    gap = target - (token_count(system) + token_count(_user_for(obj)))
    if gap > 0:
        obj["_padding"] = " ".join(["x"] * gap)   # inert budget filler: no content, no governance
    return {"condition": "E_budget_matched_status_stripped", "system": system,
            "messages": [{"role": "user", "content": _user_for(obj)}], "slice_source": case_id}


_BUILDERS = {"A_baseline_full_context": _messages_A, "B_normal_desi": _messages_B,
             "C_wrong_slice": _messages_C, "D_status_stripped": _messages_D,
             "E_budget_matched_status_stripped": _messages_E}


def build_condition(case_id: str, condition: str) -> dict:
    """Build the message payload + deterministic token-budget estimate for one (case, condition)."""
    payload = _BUILDERS[condition](case_id)
    payload["case_id"] = case_id
    payload["input_token_estimate"] = (
        token_count(payload["system"])
        + sum(token_count(m["content"]) for m in payload["messages"]))
    payload["n_messages"] = len(payload["messages"])
    return payload
