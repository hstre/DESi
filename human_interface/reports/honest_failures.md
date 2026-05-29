# Honest failure report — usability campaign

## What this campaign did NOT achieve

- **No real user test.** The success criterion is that an independent non-technical user says “I understand what DESi can do for me” without reading the paper. I built the Home/Wizard/workflows to make that true, but I have NOT run a study with a real user — so the claim is *designed-for*, not *measured*. That is the honest gap.
- **Two workflows still need a file in hand.** `check` needs a document and `decide` needs a small JSON; a true novice still has to produce that JSON. The wizard guides but does not author it.
- **Memory Explorer reflects only repo state.** It surfaces real conflicts/questions from existing reports, but it is not a live personal memory — the visionary 'personal/LLM memory' ideas were honestly rejected as not-yet-buildable.
- **The CLI is still a terminal.** A genuinely non-technical user may not open a terminal at all; a real GUI/web front-end was out of scope. Reported, not hidden.

## What it did achieve

- 12 user-visible front doors built; 4 scope-inflating ideas honestly rejected; every internal term routed through a plain-language layer.
- The single biggest win is structural: the FIRST thing a user meets is now `python desi.py` (a 30-second Home), not a 704-line paper.

## No overclaiming

- This makes DESi *more approachable*; it does not make DESi *complete*, *correct*, or *proven useful by users*. No usability metric was optimized for its own sake.
