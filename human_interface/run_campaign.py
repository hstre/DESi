"""Run the Human-Interface Evolution campaign and write the six required reports.

Process: the Wild Brother emits critiques + ideas (4 roles) -> the UX-fitness harness
(governance) decides BUILD/SPEC/REJECT deterministically -> we report what was built, what the
Wild Brother proposed, what was rejected (with reasons), the utility ranking, honest failures,
and which Wild-Brother ideas were adopted. Honest about scale: the "loops" are real idea
evaluations; we report the true count, not a fabricated 2500.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "src"))

from fitness import run_fitness  # noqa: E402
from wild_brother import CRITIQUES, IDEAS, critiques_by_role  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"

# what actually got SHIPPED this campaign (the visible artifacts) + which idea each realizes
SHIPPED = {
    "home_landing": "desi.py home  (one-screen DESi Home)",
    "what_can_you_do": "desi.py home  (plain 'what can DESi do for me' list)",
    "one_click_workflows": "desi.py check / decide / memory  (one-line workflows)",
    "plain_cli": "desi.py  (single entry point, no module paths / sys.path)",
    "run_on_my_file": "desi.py check <your-file>  (runs on the USER's file, not a probe)",
    "glossary_translation": "human_interface/glossary.py  (plain-language layer)",
    "hide_governance_jargon": "glossary.say() applied across the surface",
    "memory_explorer": "desi.py memory  (conflicts / open questions / recent work)",
    "wizard_no_jargon": "desi.py wizard + human_interface/wizard.py (plain questions only)",
    "payoff_preview": "Home shows the concrete output you get before any setup",
    "desi_as_paper_coach": "framing: 'check' presented as a paper coach (naming only)",
    "desi_as_decision_buddy": "framing: 'decide' presented as a decision buddy (naming only)",
}


def run() -> dict:
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    fit = run_fitness()
    (_RESULTS / "fitness_ledger.json").write_text(json.dumps(fit, indent=2) + "\n", encoding="utf-8")

    builds = [r for r in fit["ledger"] if r["decision"] == "BUILD"]
    specs = [r for r in fit["ledger"] if r["decision"] == "SPEC"]
    rejects = [r for r in fit["ledger"] if r["decision"] == "REJECT"]

    _ux_improvements(builds, specs)
    _wild_brother_report()
    _rejected(rejects, specs)
    _utility_ranking(fit)
    _honest_failures(fit, builds, rejects)
    _adopted(builds, specs)

    print(f"human-interface: ideas={fit['n']} BUILD={len(builds)} SPEC={len(specs)} "
          f"REJECT={len(rejects)} critiques={len(CRITIQUES)} shipped={len(SHIPPED)} "
          f"hash={fit['replay_hash'][:12]}")
    return {"n": fit["n"], "counts": fit["counts"], "shipped": len(SHIPPED),
            "replay_hash": fit["replay_hash"]}


def _ux_improvements(builds, specs):
    md = ["# Top UX improvements — ranked by human-usability fitness\n",
          f"Built this campaign: **{len(builds)}**, specced: **{len(specs)}**. "
          "(Honest: real survivor count, not a forced 'Top 20'.)\n",
          "## BUILT (fitness ≥ 7) — all user-visible\n",
          "| rank | idea | fitness | role | shipped as |", "| --- | --- | --- | --- | --- |"]
    for n, r in enumerate(builds, 1):
        md.append(f"| {n} | `{r['idea_id']}` | {r['fitness']} | {r['role']} | "
                  f"{SHIPPED.get(r['idea_id'], '—')} |")
    md += ["", "## SPECCED (fitness ≥ 3, not built)\n", "| idea | fitness | role |", "| --- | --- | --- |"]
    for r in specs:
        md.append(f"| `{r['idea_id']}` | {r['fitness']} | {r['role']} |")
    md += ["", "## The visible artifacts shipped\n",
           "- **DESi Home** (`python desi.py`): one screen — what it does, what you can do, where to start.",
           "- **One-click workflows**: `check` (paper), `decide` (options→recommendation+trade-off), "
           "`memory` (what needs attention) — each a single line.",
           "- **Memory Explorer** (`desi.py memory`): conflicts / open questions / recent work, in plain words.",
           "- **Jargon-free Wizard** (`desi.py wizard`): plain questions → the exact command; no internal terms.",
           "- **Plain-language layer** (`glossary.py`): every internal term translated at the surface.",
           "- All workflows reuse the already-built engines (paper auditor, decision recorder) — "
           "no new backend, only new front doors."]
    (_REPORTS / "top_ux_improvements.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _wild_brother_report():
    by_role = critiques_by_role()
    md = ["# The Wild Brother — top critiques & proposals\n",
          "He is rewarded for QUESTIONING, not for being right. Governance (the fitness harness) "
          "decided which proposals to act on. He may attack anything EXCEPT the protected core.\n"]
    role_titles = {"confused": "Role 1 — the confused user", "lazy": "Role 2 — the lazy user",
                   "heretical": "Role 3 — the heretical user", "visionary": "Role 4 — the visionary"}
    for role in ("confused", "lazy", "heretical", "visionary"):
        md += [f"## {role_titles[role]}\n"]
        for c in by_role[role]:
            md.append(f"- **{c.target}:** “{c.objection}”")
        md.append("")
    md += ["## His proposals (governance decides later)\n",
           "| idea | role | kind | pitch |", "| --- | --- | --- | --- |"]
    for i in IDEAS:
        md.append(f"| `{i.id}` | {i.role} | {i.kind} | {i.pitch} |")
    (_REPORTS / "wild_brother.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _rejected(rejects, specs):
    md = ["# Rejected / deferred ideas — with reasons\n",
          "Honest negatives. The fitness harness (governance) rejects forbidden or non-buildable "
          "ideas; the Wild Brother is NOT penalized for proposing them.\n",
          "## Rejected\n", "| idea | role | fitness | reason |", "| --- | --- | --- | --- |"]
    for r in rejects:
        md.append(f"| `{r['idea_id']}` | {r['role']} | {r['fitness']} | {r['reject_reason']} |")
    md += ["", "## Deferred to spec (real but not built now)\n", "| idea | role | fitness |",
           "| --- | --- | --- |"]
    for r in specs:
        md.append(f"| `{r['idea_id']}` | {r['role']} | {r['fitness']} |")
    md += ["", "## Notable rejections\n",
           "- `desi_voice_assistant`, `desi_mobile_app` — not buildable deterministically now; pure "
           "scope inflation, near-zero usability fitness. Honest no.",
           "- `desi_llm_memory`, `desi_personal_memory` — visionary framings with no buildable, "
           "user-visible artifact this campaign; deferred, not faked.",
           "- The Wild Brother proposed all four; he is credited for raising them even though "
           "governance declined — questioning is the job, being right is not required."]
    (_REPORTS / "rejected_ideas.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _utility_ranking(fit):
    md = ["# Utility ranking — usability fitness of every idea\n",
          "fitness = understandable + fewer_clicks + fewer_terms + faster_start + reusability + "
          "visible − complexity − paper_language − extra_menus.\n",
          "| rank | idea | fitness | decision |", "| --- | --- | --- | --- |"]
    for n, r in enumerate(sorted(fit["ledger"], key=lambda x: -x["fitness"]), 1):
        md.append(f"| {n} | `{r['idea_id']}` | {r['fitness']} | {r['decision']} |")
    md += ["", "## Reading\n",
           "- Top = simple, visible, jargon-removing front doors (Home, one-click workflows, plain CLI). "
           "These are where real human usability is won.",
           "- Bottom = absurd scope inflation (voice/mobile). Low fitness is correct: they add "
           "complexity and zero immediate usability."]
    (_REPORTS / "utility_ranking.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _honest_failures(fit, builds, rejects):
    md = ["# Honest failure report — usability campaign\n",
          "## What this campaign did NOT achieve\n",
          "- **No real user test.** The success criterion is that an independent non-technical user "
          "says “I understand what DESi can do for me” without reading the paper. I built the "
          "Home/Wizard/workflows to make that true, but I have NOT run a study with a real user — so "
          "the claim is *designed-for*, not *measured*. That is the honest gap.",
          "- **Two workflows still need a file in hand.** `check` needs a document and `decide` needs "
          "a small JSON; a true novice still has to produce that JSON. The wizard guides but does not "
          "author it.",
          "- **Memory Explorer reflects only repo state.** It surfaces real conflicts/questions from "
          "existing reports, but it is not a live personal memory — the visionary 'personal/LLM "
          "memory' ideas were honestly rejected as not-yet-buildable.",
          "- **The CLI is still a terminal.** A genuinely non-technical user may not open a terminal "
          "at all; a real GUI/web front-end was out of scope. Reported, not hidden.",
          "",
          "## What it did achieve\n",
          f"- {len(builds)} user-visible front doors built; {len(rejects)} scope-inflating ideas "
          "honestly rejected; every internal term routed through a plain-language layer.",
          "- The single biggest win is structural: the FIRST thing a user meets is now `python desi.py` "
          "(a 30-second Home), not a 704-line paper.",
          "",
          "## No overclaiming\n",
          "- This makes DESi *more approachable*; it does not make DESi *complete*, *correct*, or "
          "*proven useful by users*. No usability metric was optimized for its own sake."]
    (_REPORTS / "honest_failures.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _adopted(builds, specs):
    adopted = [r for r in builds if r["idea_id"] in SHIPPED]
    md = ["# Wild-Brother ideas that were adopted\n",
          f"Of the Wild Brother's {len(IDEAS)} proposals, **{len(adopted)}** were built and "
          f"**{len(specs)}** deferred to spec. Adopted (shipped) ideas:\n",
          "| idea | role | shipped as |", "| --- | --- | --- |"]
    for r in adopted:
        md.append(f"| `{r['idea_id']}` | {r['role']} | {SHIPPED[r['idea_id']]} |")
    md += ["", "## Direct line from critique to fix\n",
           "- *confused:* “where do I start?” → **DESi Home** + **Wizard**.",
           "- *lazy:* “too many terms / clicks / settings” → **plain CLI**, **one-click workflows**, "
           "**glossary layer**.",
           "- *heretical:* “only for the paper?” → **run-on-MY-file** `check`, **Memory Explorer** on "
           "real state, governance jargon hidden.",
           "- *visionary:* “sell me a coach/buddy, not 'governance'” → **Paper Coach** / **Decision "
           "Buddy** framings adopted; voice/mobile/LLM-memory honestly declined."]
    (_REPORTS / "wild_brother_adopted.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
