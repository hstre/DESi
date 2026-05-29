# Top UX improvements — ranked by human-usability fitness

Built this campaign: **12**, specced: **1**. (Honest: real survivor count, not a forced 'Top 20'.)

## BUILT (fitness ≥ 7) — all user-visible

| rank | idea | fitness | role | shipped as |
| --- | --- | --- | --- | --- |
| 1 | `home_landing` | 12 | confused | desi.py home  (one-screen DESi Home) |
| 2 | `one_click_workflows` | 12 | lazy | desi.py check / decide / memory  (one-line workflows) |
| 3 | `plain_cli` | 11 | lazy | desi.py  (single entry point, no module paths / sys.path) |
| 4 | `run_on_my_file` | 11 | heretical | desi.py check <your-file>  (runs on the USER's file, not a probe) |
| 5 | `what_can_you_do` | 10 | confused | desi.py home  (plain 'what can DESi do for me' list) |
| 6 | `glossary_translation` | 9 | lazy | human_interface/glossary.py  (plain-language layer) |
| 7 | `payoff_preview` | 9 | heretical | Home shows the concrete output you get before any setup |
| 8 | `wizard_no_jargon` | 9 | lazy | desi.py wizard + human_interface/wizard.py (plain questions only) |
| 9 | `desi_as_decision_buddy` | 8 | visionary | framing: 'decide' presented as a decision buddy (naming only) |
| 10 | `desi_as_paper_coach` | 8 | visionary | framing: 'check' presented as a paper coach (naming only) |
| 11 | `hide_governance_jargon` | 8 | heretical | glossary.say() applied across the surface |
| 12 | `memory_explorer` | 7 | heretical | desi.py memory  (conflicts / open questions / recent work) |

## SPECCED (fitness ≥ 3, not built)

| idea | fitness | role |
| --- | --- | --- |
| `desi_as_knowledge_nav` | 6 | visionary |

## The visible artifacts shipped

- **DESi Home** (`python desi.py`): one screen — what it does, what you can do, where to start.
- **One-click workflows**: `check` (paper), `decide` (options→recommendation+trade-off), `memory` (what needs attention) — each a single line.
- **Memory Explorer** (`desi.py memory`): conflicts / open questions / recent work, in plain words.
- **Jargon-free Wizard** (`desi.py wizard`): plain questions → the exact command; no internal terms.
- **Plain-language layer** (`glossary.py`): every internal term translated at the surface.
- All workflows reuse the already-built engines (paper auditor, decision recorder) — no new backend, only new front doors.
