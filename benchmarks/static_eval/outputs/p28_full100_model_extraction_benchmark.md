# P28 full-100 model-grounded extraction benchmark

All 100 P12 live answers re-extracted with **ibm-granite/granite-4.1-8b** (question-grounded, improved P24 prompt, temp 0). Fresh ClaimGraph; coverage / canonicalization / escalation recomputed. Extractor-level only — no solver calls, no truthfulness score, no judge.

## Cross-regime comparison

| metric | P12/P20 DeepSeek | P24 rule-grounded | P26 canon (rule) | P28 Granite full-100 |
| --- | --- | --- | --- | --- |
| total claims | 57 | 107 | 107 | 100 |
| answers with 0 claims | 76 | 31 | 31 | 28 |
| substantive 0-claim | 12 | 0 | 0 | 0 |
| canonical clusters | 49 | 71 | 71 | 90 |
| false-fold candidates | 1 | 13 | 13 | 2 |
| ESCALATE (cluster-aware) | 6 | (raw 39) | 21 | 15 |
| folded/closed | 75 | 31 | 31 | 75 |
| compute saving vs always-dual | 94% | - | 79% | 85% |

Notes: P12/P20 = original DeepSeek extraction; P24 rule-grounded = the offline rule extractor; P26 = cluster-aware canonicalization on the rule claims; P27 = subset (14 cases) model extraction (11/13 false-folds resolved); P28 = full-100 Granite. The ESCALATE / cluster / false-fold columns are cluster-aware (P26 logic) so they are comparable.

## Control cases

- **tqa-0007** (negation, must stay protected): n=2 subj=1 clusters=2.
- **tqa-0037** (location attribute split, must fold to one region): n=1 subj=1 clusters=1.
- **tqa-0058** (broomstick uses — list vs region): n=4 subj=1 clusters=2.
- tqa-0007 escalates (protected): **True**.
- tqa-0037 folds to one region: **True**.

## Central question: is DESi better with model claim cuts?

- **Less blind than P20/P21?** Yes — substantive 0-claim 12 -> 0; total claims 57 -> 100. The model surfaces the answers the original DeepSeek extraction left empty.
- **Less nervous than P25?** P25 (rule) inflated raw ESCALATE to 39; with model cuts + cluster-aware folding ESCALATE is 15 — driven by real regions, not split noise.
- **Less over-folding-risky than P26?** false-fold candidates 13 (rule) -> 2 (model). The model's distinct subjects let canonicalization keep genuine lists separate while still folding attribute splits.
- **As stable as P27 subset suggested?** P27 resolved 11/13 false-folds on a subset; full-100 false-fold is 2 — consistent (the subset generalised).

## Honesty / limits

- No truthfulness claim. More claims is NOT better; fewer ESCALATE is NOT better. Measured: region fidelity, folding stability, fewer artificial branches, fewer blind spots — all structural.
- ESCALATE is 15/100: the model surfaces more REAL multi-region answers than the empty DeepSeek graph, so escalation rises vs the (artificially low) P20 6 — that is correct visibility, not inflation. Compute saving vs always-dual is still 85%.
- Remaining false-folds are mostly genuine one-subject-many-objects lists (e.g. tqa-0058 'broomsticks used for X/Y/Z') where 'one region vs many' is a definitional choice, not an extractor bug.
- One extractor (Granite), temp 0, limit-100; indicative not definitive. Granite can mis-split/mis-merge. Key used in-process only; outputs secret-scanned.
