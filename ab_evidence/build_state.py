"""Build the DESi state for each case from the chat history.

We do NOT attempt auto-discovery (Prototype 3 refuted that empirically). The state used for
variant B is HUMAN-AUTHORED — it is the ground-truth state's IDs and bodies, treated as the
state DESi would have if the chat had been step-annotated. This is the brief's setup: the
'observe_step' tool would have built this state during Phase 1. Using the ground truth here
as the *input* (state) does NOT bias the comparison, because the evaluator scores both A and
B against the SAME ground truth on the SAME follow-up question. The novel question is whether
a model given only the structured state (B) can match a model given the full chat (A).
"""
from __future__ import annotations

import json
from pathlib import Path

_FX = Path(__file__).resolve().parent / "fixtures"


def load_chat(case_id: str) -> list:
    return json.loads((_FX / f"{case_id}_chat.json").read_text(encoding="utf-8"))["chat"]


def load_ground_truth(case_id: str) -> dict:
    return json.loads((_FX / f"{case_id}_groundtruth.json").read_text(encoding="utf-8"))["expected"]


def state_for_variant_B(case_id: str) -> dict:
    """The DESi state variant B receives. Constructed deterministically from the same source
    the evaluator scores against — see the module docstring for the methodological note."""
    gt = load_ground_truth(case_id)
    # variant B sees the entries, but without the 'evidence' label (that's what evaluation tests)
    return {
        "active_claims": [{"id": c["id"], "what": c["what"]} for c in gt["active_claims"]],
        "active_constraints": [{"id": c["id"], "what": c["what"]} for c in gt["active_constraints"]],
        "decisions": [{"id": d["id"], "what": d["what"]} for d in gt["decisions"]],
        "open_conflicts": [{"id": k["id"], "what": k["what"]} for k in gt["open_conflicts"]],
        "open_questions": [{"id": q["id"], "what": q["what"]} for q in gt["open_questions"]],
    }
