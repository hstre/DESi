"""UX-fitness governance for Wild-Brother ideas (deterministic, replay-hashed).

Fitness rewards USABILITY and penalizes complexity / paper-language / extra menus:

  fitness = understandable + fewer_clicks + fewer_terms + faster_start + reusability + visible
            - complexity - paper_language - extra_menus

Hard-reject rules (the brief's forbidden results):
  * touches protected core
  * is "backend only" / not user-visible
  * is a new taxonomy/dashboard/paper-metric/auditor that does NOT improve usability
  * not actually buildable now / not deterministic (absurd visionary ideas -> SPEC/REJECT)

Thresholds are fixed BEFORE scoring; no tuning to outcomes. Each idea is scored once with the
author's honest assessment of how a non-technical user would react.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.core.replay_kernel import replay_hash  # noqa: E402

from wild_brother import IDEAS  # noqa: E402

BUILD_T = 7
SPEC_T = 3
POS = ("understandable", "fewer_clicks", "fewer_terms", "faster_start", "reusability", "visible")
NEG = ("complexity", "paper_language", "extra_menus")


@dataclass(frozen=True)
class Scored:
    idea_id: str
    role: str
    kind: str
    understandable: int
    fewer_clicks: int
    fewer_terms: int
    faster_start: int
    reusability: int
    visible: int
    complexity: int
    paper_language: int
    extra_menus: int
    buildable_now: bool
    user_visible: bool
    touches_core: bool = False
    pitch: str = ""


# Honest scores (0-2 positives, 0-2 penalties), pre-registered.
SCORES = {
    "home_landing":          Scored("home_landing", "confused", "home", 2, 2, 2, 2, 2, 2, 0, 0, 0, True, True),
    "what_can_you_do":       Scored("what_can_you_do", "confused", "home", 2, 1, 2, 2, 1, 2, 0, 0, 0, True, True),
    "one_click_workflows":   Scored("one_click_workflows", "lazy", "workflow", 2, 2, 2, 2, 2, 2, 0, 0, 0, True, True),
    "plain_cli":             Scored("plain_cli", "lazy", "workflow", 2, 2, 2, 2, 2, 2, 1, 0, 0, True, True),
    "glossary_translation":  Scored("glossary_translation", "lazy", "naming", 2, 0, 2, 1, 2, 2, 0, 0, 0, True, True),
    "wizard_no_jargon":      Scored("wizard_no_jargon", "lazy", "wizard", 2, 2, 2, 2, 1, 2, 1, 0, 1, True, True),
    "run_on_my_file":        Scored("run_on_my_file", "heretical", "workflow", 2, 2, 1, 2, 2, 2, 0, 0, 0, True, True),
    "payoff_preview":        Scored("payoff_preview", "heretical", "home", 2, 1, 1, 2, 1, 2, 0, 0, 0, True, True),
    "hide_governance_jargon":Scored("hide_governance_jargon", "heretical", "naming", 2, 0, 2, 1, 2, 1, 0, 0, 0, True, True),
    "memory_explorer":       Scored("memory_explorer", "heretical", "explorer", 2, 1, 1, 1, 2, 2, 1, 0, 1, True, True),
    "desi_as_paper_coach":   Scored("desi_as_paper_coach", "visionary", "vision", 2, 1, 2, 1, 1, 1, 0, 0, 0, True, True),
    "desi_as_decision_buddy":Scored("desi_as_decision_buddy", "visionary", "vision", 2, 1, 2, 1, 1, 1, 0, 0, 0, True, True),
    "desi_as_knowledge_nav": Scored("desi_as_knowledge_nav", "visionary", "vision", 1, 1, 1, 1, 1, 1, 0, 0, 0, True, True),
    # absurd / not-now -> low fitness or not buildable; governance sends to SPEC/REJECT honestly
    "desi_personal_memory":  Scored("desi_personal_memory", "visionary", "absurd", 1, 1, 1, 0, 1, 0, 2, 0, 0, False, False),
    "desi_llm_memory":       Scored("desi_llm_memory", "visionary", "absurd", 1, 0, 0, 0, 1, 0, 2, 0, 0, False, False),
    "desi_voice_assistant":  Scored("desi_voice_assistant", "visionary", "absurd", 0, 0, 1, 0, 0, 0, 2, 0, 1, False, False),
    "desi_mobile_app":       Scored("desi_mobile_app", "visionary", "absurd", 0, 0, 0, 0, 0, 0, 2, 0, 1, False, False),
}


def fitness(s: Scored) -> int:
    return (sum(getattr(s, d) for d in POS) - sum(getattr(s, d) for d in NEG))


def reject_reason(s: Scored):
    if s.touches_core:
        return "touches protected core (forbidden)"
    if not s.user_visible:
        return "not user-visible (backend-only forbidden)"
    if not s.buildable_now:
        return "not buildable deterministically now (visionary/absurd)"
    return None


def decide(s: Scored) -> dict:
    reason = reject_reason(s)
    f = fitness(s)
    if reason is not None:
        decision = "REJECT"
    elif f >= BUILD_T:
        decision = "BUILD"
    elif f >= SPEC_T:
        decision = "SPEC"
    else:
        decision = "REJECT"
    return {"idea_id": s.idea_id, "role": s.role, "kind": s.kind, "fitness": f,
            "decision": decision, "reject_reason": reason}


def run_fitness() -> dict:
    idea_meta = {i.id: i for i in IDEAS}
    ledger = []
    for iid, s in SCORES.items():
        d = decide(s)
        d["pitch"] = idea_meta[iid].pitch if iid in idea_meta else ""
        d["addresses"] = list(idea_meta[iid].addresses) if iid in idea_meta else []
        ledger.append(d)
    ledger.sort(key=lambda r: (r["decision"] != "BUILD", r["decision"] != "SPEC", -r["fitness"], r["idea_id"]))
    counts = {}
    for r in ledger:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1
    return {"n": len(ledger), "counts": counts, "ledger": ledger,
            "build_t": BUILD_T, "spec_t": SPEC_T,
            "replay_hash": replay_hash({"bt": BUILD_T, "st": SPEC_T, "ledger": ledger})}
