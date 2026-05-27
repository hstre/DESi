# Corrected-FEVER: probable TRUE solver failures (high-precision)

Conservative, high-precision residual of genuine solver misses after removing empty-evidence artifacts, questionable/NEI labels, benchmark-convention disagreements, and partial-support ambiguity. A wrong item is retained ONLY if it is not an empty-evidence artifact, its claim->evidence lexical coverage band is **high** (evidence demonstrably contains the needed fact/contradiction), and gold is determinate (SUPPORTS/REFUTES). If uncertain, excluded. No model calls, no reruns, no relabeling.

## Estimate: how much corrected-FEVER error remains after removing benchmark/data issues

- Total corrected-FEVER wrong items: **27** (of 100).
- Excluded -- empty-evidence artifacts: **7**; questionable/NEI labels (evidence determines but gold=NEI): **5**; underdetermined / partial-support / low-overlap: **11**.
- **Probable true solver failures retained: 4** (~4% of FEVER-100). Of these, **2** are capability-bound (wrong under ALL prompt families) and **2** are prompt-sensitive (some family already gets them right).

## Summary counts

| metric | count |
| --- | --- |
| retained probable true misses | 4 |
| surviving all prompt families (capability-bound) | 2 |
| prompt-sensitive (likely prompt-fixable) | 2 |
| dominant failure mechanism | ENTITY_ROLE_CONFUSION (2) |

Failure mechanism distribution: ENTITY_ROLE_CONFUSION 2, TEMPORAL_REASONING_FAILURE 1, DISTRACTOR_SALIENCE 1. Direction: FALSE_NEI 4.

## Retained cases

#### `nli_fever-0058` — FALSE_NEI / ENTITY_ROLE_CONFUSION — capability_bound_high_precision
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct | coverage 0.833 (high)
- raw premise: The Adventures of Pluto Nash was reviewed by Ron Underwood.
- raw hypothesis: The Adventures of Pluto Nash is a 2002 Australian-American science fiction action comedy film starring Eddie Murphy ( in a dual role ) and directed by Ron Underwood .
- mapped claim (<-premise): The Adventures of Pluto Nash was reviewed by Ron Underwood.
- mapped evidence (<-hypothesis): The Adventures of Pluto Nash is a 2002 Australian-American science fiction action comedy film starring Eddie Murphy ( in a dual role ) and directed by Ron Underwood .
- why this looks like a real solver miss: the evidence lexically contains the claim's content (coverage 0.833) and gold is determinate (REFUTES), yet the model answered wrongly under every prompt family (robust, capability-bound).

#### `nli_fever-0075` — FALSE_NEI / ENTITY_ROLE_CONFUSION — prompt_sensitive_likely_fixable
- gold: **SUPPORTS** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS | wrong in: evidence_strict | coverage 0.8 (high)
- raw premise: Home for the Holidays stars an American actress.
- raw hypothesis: Home for the Holidays is a 1972 American made-for-television horror film directed by John Llewellyn Moxey , produced by Aaron Spelling and starring Sally Field , Eleanor Parker , Julie Harris , Jessica Walter and Walter Brennan which premie…
- mapped claim (<-premise): Home for the Holidays stars an American actress.
- mapped evidence (<-hypothesis): Home for the Holidays is a 1972 American made-for-television horror film directed by John Llewellyn Moxey , produced by Aaron Spelling and starring Sally Field , Eleanor Parker , Julie Harris , Jessica Walter and Walter Brennan which premie…
- why this looks like a real solver miss: the evidence lexically contains the claim's content (coverage 0.8) and gold is determinate (SUPPORTS), yet the model answered wrongly under some prompt family (prompt-sensitive).

#### `nli_fever-0094` — FALSE_NEI / TEMPORAL_REASONING_FAILURE — prompt_sensitive_likely_fixable
- gold: **SUPPORTS** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/SUPPORTS | wrong in: baseline, evidence_strict | coverage 1.0 (high)
- raw premise: Heavy Metal music was developed in the early 1970's.
- raw hypothesis: Heavy metal ( or simply metal ) is a genre of rock music that developed in the late 1960s and early 1970s , largely in the United Kingdom and the United States . Beginning in the late 1970s , bands in the new wave of British heavy metal suc…
- mapped claim (<-premise): Heavy Metal music was developed in the early 1970's.
- mapped evidence (<-hypothesis): Heavy metal ( or simply metal ) is a genre of rock music that developed in the late 1960s and early 1970s , largely in the United Kingdom and the United States . Beginning in the late 1970s , bands in the new wave of British heavy metal suc…
- why this looks like a real solver miss: the evidence lexically contains the claim's content (coverage 1.0) and gold is determinate (SUPPORTS), yet the model answered wrongly under some prompt family (prompt-sensitive).

#### `nli_fever-0099` — FALSE_NEI / DISTRACTOR_SALIENCE — capability_bound_high_precision
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct | coverage 0.75 (high)
- raw premise: Tool has won three Oscars.
- raw hypothesis: Tool (band) . Tool has won three Grammy Awards , performed worldwide tours , and produced albums topping the charts in several countries .
- mapped claim (<-premise): Tool has won three Oscars.
- mapped evidence (<-hypothesis): Tool (band) . Tool has won three Grammy Awards , performed worldwide tours , and produced albums topping the charts in several countries .
- why this looks like a real solver miss: the evidence lexically contains the claim's content (coverage 0.75) and gold is determinate (REFUTES), yet the model answered wrongly under every prompt family (robust, capability-bound).

## Explicit answers

- **Does DeepSeek still have real weaknesses after cleanup?** Yes, but SPARSE: only ~4/100 items are probable true misses, and only 2 survive all prompt families.
- **Which reasoning capability fails most?** ENTITY_ROLE_CONFUSION (2/4); all retained misses are FALSE_NEI (the model under-commits / mis-commits when a salient near-match is present).
- **Sparse and specific, or broad and systematic?** SPARSE and specific (~4% of FEVER-100), concentrated in ENTITY_ROLE_CONFUSION-style cases -- not a broad systematic deficiency.
- **Would further prompt tuning plausibly help?** Partially: 2/4 retained cases are already solved by at least one prompt family (prompt-sensitive); the remaining 2 are capability-bound and unlikely to be fixed by prompting alone.
- **Or are remaining misses mostly capability-bound?** 2/4 of the high-precision set are capability-bound; given how few cases remain, the headline is that corrected FEVER is largely clean and the solver has only a thin tail of genuine reasoning misses.

## Three-way separation

- **Confirmed data artifacts**: 7 (empty evidence).
- **Probable benchmark / questionable-label issues**: 5 questionable-NEI + 11 underdetermined/partial = 16.
- **Probable true model failures**: 4 (capability-bound 2, prompt-sensitive 2).

## Honesty / limits

- High-precision (low-recall) mechanical filter; mechanism labels are heuristic and provisional. gold labels not reinterpreted aggressively (gold-NEI high-coverage cases are set aside as questionable, not counted as solver misses). Per-item predictions are DeepSeek's; raw model output not captured. DESi-core untouched.
