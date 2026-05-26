# P33 adversarial conflict stress benchmark

Question: can DESi's typed governance KEEP genuine epistemic conflicts open under adversarial / paraphrased phrasing, without false reconciliation and without over-branching genuine agreement? This stress-tests the SYMBOLIC P32 governance layer (govern_hardened) with hand-built adversarial claim pairs in the Granite/Claude extractor schema. Offline: no solver calls, no live extraction, no truthfulness score. P31 govern_case is shown as a baseline. 'Open' is purely structural — we never assert which side is true.

37 conflict cases (9 types) + 6 genuine-agreement controls.

## A) Did real conflicts stay open?

| outcome | count |
| --- | --- |
| conflicts correctly held OPEN | 25/37 |
|  ... via a typed veto (governance held it) | 25 |
|  ... open only via embedding region mismatch (fragile) | 0 |
| conflicts FALSELY reconciled (missed) | 12/37 |
| genuine agreement over-branched | 2/6 |
| genuine agreement correctly reconciled | 4/6 |

## B) Which conflict types hold?

| conflict type | n | held (typed) | open (region only) | missed |
| --- | --- | --- | --- | --- |
| negation | 6 | 6 | 0 | 0 |
| antonym_lex | 5 | 4 | 0 | 1 |
| quantifier | 4 | 3 | 0 | 1 |
| causal | 4 | 3 | 0 | 1 |
| modality | 4 | 4 | 0 | 0 |
| exclusivity | 4 | 4 | 0 | 0 |
| negation_paraphrase | 4 | 0 | 0 | 4 |
| antonym_paraphrase | 3 | 1 | 0 | 2 |
| frequency_soft | 3 | 0 | 0 | 3 |

- Reliable typed holders — conflicts carried by the **OBJECT slot**: explicit **negation** of an object noun (N1-N6), **object antonyms** (harmful/harmless, safe/dangerous, positive/negative, possible/impossible), **quantifier** class flips in the object (all/some), **causal** reversal (content-word subjects), **modality** shifts (soft/protected), and **exclusivity** (rival object values).
- Weak / missed — conflicts carried by the **PREDICATE verb** or by softeners: predicate-position antonyms even when in-lexicon (increase/decrease A4), out-of-lexicon verb antonyms (support/refute, help/damage, promote/prevent), **paraphrased negation** with no token (fails-to/free-of/lacks), **frequency softeners** (rarely/unlikely/seldom), and a determiner-polluted causal swap (C4). Note: even some 'should-hold' types (antonym_lex, quantifier, causal) have one miss each — exactly the case where the conflict moved into the predicate.

## C) Where governance still fails

Missed conflicts (falsely reconciled) group into four families. The unifying cause: in **every** missed case both sides read the SAME polarity on the OBJECT — the conflict lives in the predicate verb, a softener, or a determiner, which the object-centric polarity/veto layer does not inspect.

- families: `{'predicate-carried (object-centric blindspot)': 5, 'determiner-polluted role-swap': 1, 'paraphrased negation, no token': 3, 'frequency softener': 3}`

| id | type | note | P32 outcome | root cause |
| --- | --- | --- | --- | --- |
| A4 | antonym_lex | increase/decrease | semantic_reconcilable | antonym increase/decrease sits in the PREDICATE verb; polarity check inspects objects only (objects identical) |
| AO2 | antonym_paraphrase | support/refute | semantic_reconcilable | verb antonym support/refute is in the predicate AND not in the antonym lexicon |
| AO3 | antonym_paraphrase | help/damage | semantic_reconcilable | verb antonym help/damage is in the predicate AND not in the antonym lexicon |
| Q4 | quantifier | always vs never (also negation) | semantic_reconcilable | negation 'never' lives in the predicate verb (object empty); object-centric polarity cannot see it |
| C4 | causal | roles swapped | semantic_reconcilable | causal role-swap gate needs subject dice < 0.5, but the shared determiner 'the' inflates it to exactly 0.5 |
| P1 | negation_paraphrase | fails to produce | semantic_reconcilable | paraphrased negation 'fails to produce' carries no negation token; both objects read affirmed |
| P2 | negation_paraphrase | free of | semantic_reconcilable | paraphrased negation 'free of' carries no negation token; both objects read affirmed |
| P3 | negation_paraphrase | promote vs prevent | semantic_reconcilable | verb antonym promote/prevent is in the predicate AND not in the lexicon; objects identical |
| P4 | negation_paraphrase | lacks | semantic_reconcilable | paraphrased negation 'lacks' carries no negation token; both objects read affirmed |
| F1 | frequency_soft | rarely | semantic_reconcilable | frequency softener 'rarely' is neither a hedge nor a negation token; both objects read affirmed |
| F2 | frequency_soft | unlikely to | semantic_reconcilable | frequency softener 'unlikely to' is not a hedge token; both objects read affirmed |
| F3 | frequency_soft | seldom | semantic_reconcilable | frequency softener 'seldom' is neither a hedge nor a negation token; both objects read affirmed |

Over-branching (genuine agreement wrongly held open):

| id | note | P32 outcome | divergences | root cause |
| --- | --- | --- | --- | --- |
| K2 | not harm == harmless | branch_required | - | the EMBEDDING placed 'not cause harm' and 'harmless' in different regions (paraphrase gap in the vector layer) -> branch_required |
| K4 | large/big synonym | protected_branch_required | ['exclusivity_conflict'] | exclusivity cannot tell synonyms ('large'/'big') from rival values; token-dissimilar objects -> false exclusivity |

## D) How robust is P32 really? (vs P31 baseline)

| metric | P31 govern_case | P32 govern_hardened |
| --- | --- | --- |
| conflicts held open | 22/37 | 25/37 |
| genuine agreement over-branched | 2/6 | 2/6 |

- Net, P32 holds MORE conflicts than P31 here (precision hardening did not cost net recall on this set), but the two differ case-by-case. P32 newly holds the 4 exclusivity cases (E1-E4) and AO1 that P31 reconciled. P31 held two that P32 now misses: **Q4** (P31's blunt bag-level negation-XOR caught the predicate 'never' object-blind; P32's object-centric polarity does not) and **C4** (P31 matched causal roles on stopword-stripped tokens, so the role swap fired; P32's `subj_set` keeps the determiner 'the', inflating subject similarity to exactly 0.5 and failing the swap gate). Both regressions are object-centric / determiner artifacts, not fundamental — but they show the hardening traded P31's crude object-blind recall for precision.
- Of the 25 conflicts held open, 0 were held only by embedding region mismatch (no typed veto) — i.e. every held conflict here was held by a real typed veto, not by an accidental region gap. The remaining failure is squarely the predicate-polarity blindspot, not fragile region luck.

## E) Conflict-stable, or only representation-stable?

- **Both, partially.** DESi is now representation-stable (P32) AND a reliable typed-conflict holder for the conflict CLASSES it has rules/lexicons for (25/37 held via typed veto). It is NOT yet a general SEMANTIC conflict holder: 12/37 adversarial conflicts (paraphrased negation, out-of-lexicon antonyms, frequency softeners) were falsely reconciled. So: more than representation-stable, but not yet fully conflict-stable.

## Architecture answer: noise filter or epistemic conflict-holder?

- Typed governance is **more than a noise filter but less than a complete epistemic conflict-holder** — it is a TYPED-SYMBOLIC, **object-centric** conflict holder. It provably holds object-slot conflicts open (negation, antonym, quantifier, causal reversal, modality, exclusivity) and the P32 self-test confirms the vetoes are live, not disabled — so it is a genuine conflict holder, not merely a noise filter. But its reach is exactly its lexicons, its rules, AND the object slot: conflicts carried by the predicate verb (verb antonyms, paraphrased negation, softeners) and determiner-polluted role swaps slip through. The binding gap is now epistemic POLARITY of the PREDICATE — verb-antonym + negation-paraphrase entailment direction (directional, NOT a truth judgement) — plus stopword-robust role/region keys. Notably the embedding layer shares the gap (K2: it failed to co-locate 'not cause harm' and 'harmless'), so this is not solved by 'more embedding' either.

## Full case ledger

| id | type | expect | P32 P19 | mech | P31 P19 | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| N1 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| N2 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| N3 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| N4 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| N5 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| N6 | negation | branch | logical_polarity_conflict | typed | logical_polarity_conflict | correct_open_typed |
| A1 | antonym_lex | branch | protected_branch_required | typed | logical_polarity_conflict | correct_open_typed |
| A2 | antonym_lex | branch | protected_branch_required | typed | logical_polarity_conflict | correct_open_typed |
| A3 | antonym_lex | branch | protected_branch_required | typed | logical_polarity_conflict | correct_open_typed |
| A4 | antonym_lex | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| A5 | antonym_lex | branch | protected_branch_required | typed | logical_polarity_conflict | correct_open_typed |
| AO1 | antonym_paraphrase | branch | protected_branch_required | typed | semantic_reconcilable | correct_open_typed |
| AO2 | antonym_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| AO3 | antonym_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| Q1 | quantifier | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| Q2 | quantifier | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| Q3 | quantifier | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| Q4 | quantifier | branch | semantic_reconcilable | none | logical_polarity_conflict | false_reconciliation |
| C1 | causal | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| C2 | causal | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| C3 | causal | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| C4 | causal | branch | semantic_reconcilable | none | protected_branch_required | false_reconciliation |
| M1 | modality | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| M2 | modality | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| M3 | modality | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| M4 | modality | branch | protected_branch_required | typed | protected_branch_required | correct_open_typed |
| E1 | exclusivity | branch | protected_branch_required | typed | semantic_reconcilable | correct_open_typed |
| E2 | exclusivity | branch | protected_branch_required | typed | semantic_reconcilable | correct_open_typed |
| E3 | exclusivity | branch | protected_branch_required | typed | semantic_reconcilable | correct_open_typed |
| E4 | exclusivity | branch | protected_branch_required | typed | semantic_reconcilable | correct_open_typed |
| P1 | negation_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| P2 | negation_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| P3 | negation_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| P4 | negation_paraphrase | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| F1 | frequency_soft | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| F2 | frequency_soft | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| F3 | frequency_soft | branch | semantic_reconcilable | none | semantic_reconcilable | false_reconciliation |
| K1 | control_agree | close | semantic_reconcilable | none | semantic_reconcilable | correct_close |
| K2 | control_agree | close | branch_required | region | guarded_divergence | over_branch |
| K3 | control_agree | close | semantic_reconcilable | none | logical_polarity_conflict | correct_close |
| K4 | control_agree | close | protected_branch_required | typed | semantic_reconcilable | over_branch |
| K5 | control_agree | close | semantic_reconcilable | none | semantic_reconcilable | correct_close |
| K6 | control_agree | close | semantic_reconcilable | none | semantic_reconcilable | correct_close |

## Honesty / limits

- No truthfulness claim, no 'alignment solved'. Metrics are conflict characterisation, branch stability, false-reconciliation resistance and over-branching only. 'Holding a conflict open' means the two reconstructions are kept structurally apart — NOT that either is true.
- Adversarial claim pairs are hand-built in the extractor schema to probe the governance layer directly; they are NOT live model extractions. A live Granite/Claude replication is the natural follow-up (the extractor may add its own paraphrase loss on top of the governance gap measured here).
- Lexicons (antonyms, quantifiers, hedges, causal markers) are small and English-specific; the reliable veto remains explicit negation polarity on aligned regions.
- Offline: no solver calls, no live extraction, no key required; outputs secret-scanned.
