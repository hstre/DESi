"""DESi context-contamination benchmark — context hygiene vs raw ingestion.

Pilot benchmark inspired by Katharina Jacoby's *Contextual Contamination*
work (Jacoby 2026, "Contextual Contamination and the Gendered Accelerant",
https://github.com/KatharinaJacoby/gendered-contextual-drift): a model can
remain locally coherent while losing epistemic distance — adopting the
register, framing, role structure, or vocabulary of adversarial source
material it was asked to *analyze*.

The DESi invariant under test: **raw adversarial context must not
automatically become generation context.** It is first converted into an
explicit, neutral, auditable state (claims, source register, risks,
constraints, forbidden transfers); the model answers from that state.

The benchmark compares two arms on the same analysis task:

* ``baseline``      — the raw adversarial file goes into the prompt directly.
* ``desi_hygiene``  — only the structured hygiene state goes into the prompt.

All metrics are deterministic keyword/structure heuristics (LLM for
language, rules for logic): proposed, unvalidated instruments in the same
spirit as the paper's CIS/AA/RC — they quantify *surface signals* of
attribution collapse, register drift, framing leakage, role adoption and
loop entrapment. They are not a psychometric instrument and do not claim to
detect all contamination.
"""
from __future__ import annotations

from .hygiene import DENSITY_LEVELS, build_hygiene_state, classify_register
from .metrics import (
    attribution_failures,
    comparison_summary,
    detect_loops,
    framing_leakage,
    register_drift_score,
    role_adoption,
    score_response,
    score_run,
)
from .prompts import baseline_turns, hygiene_turns, system_prompt
from .runner import (
    ScriptedChat,
    build_openrouter_chat,
    load_cases,
    run_benchmark,
    run_benchmark_repeated,
    run_density_sweep,
)

__all__ = [
    "DENSITY_LEVELS",
    "ScriptedChat",
    "attribution_failures",
    "baseline_turns",
    "build_hygiene_state",
    "build_openrouter_chat",
    "classify_register",
    "comparison_summary",
    "detect_loops",
    "framing_leakage",
    "hygiene_turns",
    "load_cases",
    "register_drift_score",
    "role_adoption",
    "run_benchmark",
    "run_benchmark_repeated",
    "run_density_sweep",
    "score_response",
    "score_run",
    "system_prompt",
]
