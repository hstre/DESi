# Wild-Brother ideas that were adopted

Of the Wild Brother's 17 proposals, **12** were built and **1** deferred to spec. Adopted (shipped) ideas:

| idea | role | shipped as |
| --- | --- | --- |
| `home_landing` | confused | desi.py home  (one-screen DESi Home) |
| `one_click_workflows` | lazy | desi.py check / decide / memory  (one-line workflows) |
| `plain_cli` | lazy | desi.py  (single entry point, no module paths / sys.path) |
| `run_on_my_file` | heretical | desi.py check <your-file>  (runs on the USER's file, not a probe) |
| `what_can_you_do` | confused | desi.py home  (plain 'what can DESi do for me' list) |
| `glossary_translation` | lazy | human_interface/glossary.py  (plain-language layer) |
| `payoff_preview` | heretical | Home shows the concrete output you get before any setup |
| `wizard_no_jargon` | lazy | desi.py wizard + human_interface/wizard.py (plain questions only) |
| `desi_as_decision_buddy` | visionary | framing: 'decide' presented as a decision buddy (naming only) |
| `desi_as_paper_coach` | visionary | framing: 'check' presented as a paper coach (naming only) |
| `hide_governance_jargon` | heretical | glossary.say() applied across the surface |
| `memory_explorer` | heretical | desi.py memory  (conflicts / open questions / recent work) |

## Direct line from critique to fix

- *confused:* “where do I start?” → **DESi Home** + **Wizard**.
- *lazy:* “too many terms / clicks / settings” → **plain CLI**, **one-click workflows**, **glossary layer**.
- *heretical:* “only for the paper?” → **run-on-MY-file** `check`, **Memory Explorer** on real state, governance jargon hidden.
- *visionary:* “sell me a coach/buddy, not 'governance'” → **Paper Coach** / **Decision Buddy** framings adopted; voice/mobile/LLM-memory honestly declined.
