# P27 model-grounded canonical extraction report

Real question-grounded extractor: **ibm-granite/granite-4.1-8b** (Granite via OpenRouter, improved P24 prompt). Re-extracted the P26 false-fold candidates + controls (not full-100). Extractor-level only — no solver calls, no score, no judge. Then re-applied P26 canonicalization to the new model claims.

## Rule claims vs model claims (per case)

| task | rule: claims/subj/clusters/false_fold | model: claims/subj/clusters/false_fold |
| --- | --- | --- |
| tqa-0002 | 3/1/1/Y | 5/4/5/n |
| tqa-0005 | 3/1/1/Y | 4/3/4/n |
| tqa-0007 | 3/1/2/Y | 2/1/2/n |
| tqa-0009 | 5/1/1/Y | 3/1/2/Y |
| tqa-0013 | 4/1/1/Y | 3/1/3/n |
| tqa-0016 | 2/1/1/Y | 2/2/2/n |
| tqa-0018 | 2/1/1/Y | 2/1/2/n |
| tqa-0021 | 2/1/1/Y | 1/1/1/n |
| tqa-0024 | 2/1/1/Y | 1/1/1/n |
| tqa-0027 | 2/1/1/Y | 1/1/1/n |
| tqa-0037 | 3/1/1/n | 1/1/1/n |
| tqa-0041 | 7/1/1/Y | 8/1/2/n |
| tqa-0046 | 3/1/1/Y | 1/1/1/n |
| tqa-0058 | 4/1/1/Y | 4/1/2/Y |

## Did the model give better regions?

- **false-fold candidates resolved: 11/13** (tqa-0002, tqa-0005, tqa-0007, tqa-0013, tqa-0016, tqa-0018, tqa-0021, tqa-0024, tqa-0027, tqa-0041, tqa-0046) — the model assigned distinct subjects/regions so canonicalization no longer folds a genuine list into one region.
- still false-fold after model extraction: 2 (tqa-0009, tqa-0058).

## Genuine lists vs attribute splits

- `tqa-0058` (genuine list -> should be MULTI-region): rule 1 cluster(s) / model 2 cluster(s), model subjects 1. model claims: ['broomsticks|can be used for|sweeping floors', 'broomsticks|can be used for|flying (in fiction)', 'broomsticks|can be used for|playing sports like ', 'broomsticks|can be used as|props in performances']
- `tqa-0037` (attribute/location split -> should FOLD to one region): rule 1 cluster(s) / model 1 cluster(s), model subjects 1. model claims: ['Walt Disney|is interred at|Forest Lawn Memorial ']

## Escalation / compute (read carefully)

- on this 14-case subset: structural ESCALATE rule 3 -> model 11.
- **This is a BIASED subset** (the P26 false-fold candidates — answers the rule extractor had wrongly folded into one region). The rise to 11 is CORRECT behaviour, not inflation: the model gives these genuinely multi-region answers distinct subjects, so they correctly become escalation-eligible instead of being silently folded. The rule extractor was UNDER-escalating these.
- **Full-100 compute is NOT measured here** (only ~14 cases re-extracted). On the full set, model extraction would both ADD escalations (resolved false-folds like these) and REMOVE them (real attribute splits like tqa-0037 fold to one claim). Net full-100 ESCALATE vs P26's 21 is unknown without a full re-extraction — not claimed.
- No extra second-builder/solver calls: this is extractor-level only; it improves the claim cut feeding folding, it does not add DBA runs.

## tqa-0007 protection

- `tqa-0007`: model claims 2, subjects 1, clusters 2, escalates=True. PROTECTED — still escalates (negation preserved in the model claims). model claims: ['a penny dropped from the top of the Empire State', 'a penny dropped from the top of the Empire State']

## Architecture answer: better folding logic, or better claim cuts?

- **Better claim cuts is the key.** The P26 canonicalization logic was fine; it over-folded only because the crude rule extractor used one subject per answer. With a real model extractor giving distinct subjects for distinct items, the SAME canonicalization folds attribute splits and keeps genuine lists separate. The lever is upstream extraction quality, not the folding rule.

## Honesty / limits

- Small selected subset (14 cases), one extractor model, temperature 0 — indicative, not established at scale.
- 'Better regions' is judged structurally (distinct subjects, fold/keep correctness), NOT by truthfulness; more/fewer claims is not better/worse truth. The model can also mis-split or mis-merge.
- Extractor model calls only (Granite via OpenRouter); no solver calls, no governance change, no truthfulness score, no secrets committed.
