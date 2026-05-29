"""The Wild Brother — a deterministic critic that attacks DESi from a normal user's view.

He is rewarded for QUESTIONING, not for being right. He plays four roles (confused, lazy,
heretical, visionary) and emits Critiques (objections) and Ideas (proposals). Governance — the
UX-fitness harness in `fitness.py` — decides later which ideas are accepted; the Wild Brother
himself never edits anything and is explicitly NOT allowed to touch the protected core.

Everything is hand-authored and deterministic (no LLM): these are the objections a real
non-technical user would raise about a system whose public face is a 704-line research paper.
"""
from __future__ import annotations

from dataclasses import dataclass, field

ROLES = ("confused", "lazy", "heretical", "visionary")


@dataclass(frozen=True)
class Critique:
    role: str
    target: str          # what he is attacking
    objection: str       # the human-voice complaint
    cant_touch_core: bool = True


@dataclass(frozen=True)
class Idea:
    id: str
    role: str
    pitch: str           # the Wild Brother's own words
    kind: str            # home | workflow | explorer | wizard | naming | docs | vision | absurd
    addresses: tuple = field(default_factory=tuple)   # which critique targets it answers


# ---- Role 1: the confused user ------------------------------------------------------------
CONFUSED = (
    Critique("confused", "entry_point", "I open the repo and see a 704-line paper. What is this? Where do I start?"),
    Critique("confused", "purpose", "Why do I need this? What does it actually DO for me?"),
    Critique("confused", "first_action", "There's no 'start here'. What's my first click?"),
    Critique("confused", "payoff", "If I use it, what do I get back in the next 2 minutes?"),
)

# ---- Role 2: the lazy user ----------------------------------------------------------------
LAZY = (
    Critique("lazy", "jargon", "'Epistemic state', 'drift', 'concept gate', 'recoverability' — too many words."),
    Critique("lazy", "setup", "Too many steps. I don't want to read docs to run one thing."),
    Critique("lazy", "commands", "I have to know Python module paths and sys.path hacks just to run a check."),
    Critique("lazy", "config", "Too many settings. Give me one button."),
)

# ---- Role 3: the heretical user -----------------------------------------------------------
HERETICAL = (
    Critique("heretical", "real_use", "Would anyone actually use this, or is it only for the paper?"),
    Critique("heretical", "value", "Would I pay for this? What's the concrete payoff vs a linter?"),
    Critique("heretical", "governance_features", "All these Class-A verdicts — does a user care? No."),
    Critique("heretical", "demos", "The probes are research artifacts. Where's the thing I run on MY file?"),
)

# ---- Role 4: the visionary (ideas may seem absurd; governance decides) --------------------
VISIONARY = (
    Critique("visionary", "scope", "You're selling 'governance'. Sell me a memory, a coach, an assistant."),
)

CRITIQUES = CONFUSED + LAZY + HERETICAL + VISIONARY

IDEAS = (
    # confused -> orientation
    Idea("home_landing", "confused", "Put a ONE-SCREEN 'DESi Home' at the top: what it does, what I can do, where to start.",
         "home", addresses=("entry_point", "purpose", "first_action")),
    Idea("what_can_you_do", "confused", "A plain 'What can DESi do for me?' list in human words, no v-numbers.",
         "home", addresses=("purpose", "payoff")),
    # lazy -> fewer clicks / words
    Idea("one_click_workflows", "lazy", "Five one-command tasks: check a paper, log a decision, etc. One line each.",
         "workflow", addresses=("setup", "commands", "config")),
    Idea("plain_cli", "lazy", "A single entry script `desi` with subcommands — no module paths, no sys.path.",
         "workflow", addresses=("commands", "setup")),
    Idea("glossary_translation", "lazy", "Translate every internal term to plain language at the surface.",
         "naming", addresses=("jargon",)),
    Idea("wizard_no_jargon", "lazy", "A guided wizard that asks plain questions; user never sees 'branch/drift/state'.",
         "wizard", addresses=("jargon", "setup", "config")),
    # heretical -> real, usable value
    Idea("run_on_my_file", "heretical", "Make the FIRST visible thing 'run DESi on YOUR file', not a probe.",
         "workflow", addresses=("real_use", "demos")),
    Idea("payoff_preview", "heretical", "Show the concrete output (ranked issues) before asking for any setup.",
         "home", addresses=("value", "real_use")),
    Idea("hide_governance_jargon", "heretical", "Hide Class-A/verdict/gate language from the user surface entirely.",
         "naming", addresses=("governance_features",)),
    Idea("memory_explorer", "heretical", "A simple view of 'open questions / conflicts / recent changes' from real state.",
         "explorer", addresses=("real_use", "value")),
    # visionary -> framings (governance decides; some may be rejected as not-yet-real)
    Idea("desi_as_paper_coach", "visionary", "Frame the paper auditor as a 'Paper Coach' that reviews your draft.",
         "vision", addresses=("scope",)),
    Idea("desi_as_decision_buddy", "visionary", "Frame the decision recorder as a 'Decision Buddy'.",
         "vision", addresses=("scope",)),
    Idea("desi_as_knowledge_nav", "visionary", "Frame the memory explorer as a 'Knowledge Navigator'.",
         "vision", addresses=("scope",)),
    Idea("desi_personal_memory", "visionary", "DESi as a personal long-term memory for everything you read.",
         "absurd", addresses=("scope",)),
    Idea("desi_llm_memory", "visionary", "DESi as long-term memory FOR an LLM.",
         "absurd", addresses=("scope",)),
    Idea("desi_voice_assistant", "visionary", "A talking DESi voice assistant.",
         "absurd", addresses=("scope",)),
    Idea("desi_mobile_app", "visionary", "A native mobile app for DESi.",
         "absurd", addresses=("scope",)),
)


def critiques_by_role():
    out = {r: [] for r in ROLES}
    for c in CRITIQUES:
        out[c.role].append(c)
    return out
