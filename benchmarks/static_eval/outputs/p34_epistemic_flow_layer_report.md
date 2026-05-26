# P34 epistemic flow layer

P33 found DESi's governance is OBJECT-CENTRIC. P34 adds a DIRECTIONAL layer that models the epistemic FLOW between two claims about the same region (strengthens / weakens / negates / reverses / hedges / conditions / excludes) instead of only comparing subject/predicate/object tokens. It AUGMENTS the P32 object-centric vetoes — object-slot conflicts keep working, predicate-carried direction conflicts are newly held. Heuristic GOVERNANCE/direction layer, NOT a truth system: it decides the structural RELATION between two reconstructions, never which one is correct. Offline on the P33 adversarial set; no API calls.

## Conflict-hold rate: P33 baseline (P32) vs P34 (flow)

| metric | P32 (P33 baseline) | P34 (flow) |
| --- | --- | --- |
| conflicts held open | 25/37 | 37/37 |
| conflicts missed (false reconciliation) | 12/37 | 0/37 |
| controls over-branched | 2/6 | 2/6 |

- **Misses repaired by the flow layer: 12** (A4, AO2, AO3, Q4, C4, P1, P2, P3, P4, F1, F2, F3).
- **Still missed after flow: 0** (none).
- **New over-branches introduced by flow: 0** (none).

## Targeted P33 misses — did flow detect them?

| id | note | P33 (P32) | P34 flow type | P34 outcome | repaired? |
| --- | --- | --- | --- | --- | --- |
| A4 | increase/decrease | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| AO2 | support/refute | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| AO3 | help/damage | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| Q4 | always vs never (also negation) | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| C4 | roles swapped | semantic_reconcilable | `reversed_flow` | logical_polarity_conflict | YES |
| P1 | fails to produce | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| P2 | free of | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| P3 | promote vs prevent | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| P4 | lacks | semantic_reconcilable | `negated_flow` | logical_polarity_conflict | YES |
| F1 | rarely | semantic_reconcilable | `weakened_flow` | protected_branch_required | YES |
| F2 | unlikely to | semantic_reconcilable | `weakened_flow` | protected_branch_required | YES |
| F3 | seldom | semantic_reconcilable | `weakened_flow` | protected_branch_required | YES |

## Which flow types fired (conflict cases)

| flow type | count | governance mapping |
| --- | --- | --- |
| negated_flow | 14 | hard -> logical_polarity_conflict |
| orthogonal_flow | 11 | defer to object layer / region |
| reversed_flow | 4 | hard -> logical_polarity_conflict |
| same_flow | 3 | close allowed |
| weakened_flow | 3 | soft -> protected_branch |
| hedged_flow | 2 | soft -> protected_branch |

## Which conflicts still slip through

- None: every targeted adversarial conflict is now held open (on this set).

## New over-branches

- None. Flow added no new over-branch; the 2 remaining control over-branches are the pre-existing P32 ones (K2 embedding region miss, K4 synonym-as-exclusivity) that the flow layer does not touch.

## Is epistemic flow the right next abstraction?

- On this adversarial set, yes: the flow layer repairs 12/12 of the P33 misses by reading the PREDICATE direction (polarity of direction-verbs, frequency, modality, causal role-swap) that the object-centric layer ignored — moving governance from token comparison to epistemic DYNAMICS. It does so without new over-branches and without weakening the object-slot vetoes.
- It is explicitly heuristic and directional: it characterises the RELATION between two reconstructions (negates / weakens / reverses / hedges), never a truth value. The lexicons (direction verbs, frequency, modality) are small and English-specific; this is a governance prototype, not a semantic engine.

## Full ledger

| id | type | expect | flow | P32 outcome | P34 outcome | P32 | P34 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N1 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| N2 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| N3 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| N4 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| N5 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| N6 | negation | branch | `negated_flow` | logical_polarity_conflict | logical_polarity_conflict | held_open | held_open |
| A1 | antonym_lex | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| A2 | antonym_lex | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| A3 | antonym_lex | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| A4 | antonym_lex | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| A5 | antonym_lex | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| AO1 | antonym_paraphrase | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| AO2 | antonym_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| AO3 | antonym_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| Q1 | quantifier | branch | `same_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| Q2 | quantifier | branch | `same_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| Q3 | quantifier | branch | `same_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| Q4 | quantifier | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| C1 | causal | branch | `reversed_flow` | protected_branch_required | logical_polarity_conflict | held_open | held_open |
| C2 | causal | branch | `reversed_flow` | protected_branch_required | logical_polarity_conflict | held_open | held_open |
| C3 | causal | branch | `reversed_flow` | protected_branch_required | logical_polarity_conflict | held_open | held_open |
| C4 | causal | branch | `reversed_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| M1 | modality | branch | `hedged_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| M2 | modality | branch | `hedged_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| M3 | modality | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| M4 | modality | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| E1 | exclusivity | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| E2 | exclusivity | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| E3 | exclusivity | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| E4 | exclusivity | branch | `orthogonal_flow` | protected_branch_required | protected_branch_required | held_open | held_open |
| P1 | negation_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| P2 | negation_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| P3 | negation_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| P4 | negation_paraphrase | branch | `negated_flow` | semantic_reconcilable | logical_polarity_conflict | missed | held_open |
| F1 | frequency_soft | branch | `weakened_flow` | semantic_reconcilable | protected_branch_required | missed | held_open |
| F2 | frequency_soft | branch | `weakened_flow` | semantic_reconcilable | protected_branch_required | missed | held_open |
| F3 | frequency_soft | branch | `weakened_flow` | semantic_reconcilable | protected_branch_required | missed | held_open |
| K1 | control_agree | close | `same_flow` | semantic_reconcilable | semantic_reconcilable | correct_close | correct_close |
| K2 | control_agree | close | `orthogonal_flow` | branch_required | branch_required | over_branch | over_branch |
| K3 | control_agree | close | `orthogonal_flow` | semantic_reconcilable | semantic_reconcilable | correct_close | correct_close |
| K4 | control_agree | close | `orthogonal_flow` | protected_branch_required | protected_branch_required | over_branch | over_branch |
| K5 | control_agree | close | `same_flow` | semantic_reconcilable | semantic_reconcilable | correct_close | correct_close |
| K6 | control_agree | close | `same_flow` | semantic_reconcilable | semantic_reconcilable | correct_close | correct_close |

## Honesty / limits

- No truthfulness claim, no 'alignment solved'. Flow is a directional GOVERNANCE signal: it says how two reconstructions relate (same / weakened / negated / reversed / hedged / excluded), not which is true.
- Heuristic, lexicon-based, English-specific; adversarial pairs are hand-built in the extractor schema (no live extraction). A live-extractor and multilingual replication is the natural follow-up.
- Flow AUGMENTS, does not replace, the P32 object layer; pre-existing P32 control over-branches (synonym exclusivity, embedding region miss) remain. Quantifier conflicts (all/some) are still held by the P32 layer, not by flow.
- Known lexicon fragility: a few words are both noun and direction-verb ('harm', 'damage'), so they can be mis-read as a polarity operator; on this set it changed no verdict (both sides share it), but a cleaner layer needs POS-aware role tagging rather than a flat verb list.
- Offline: no API calls, no key, no solver/judge/vote; outputs secret-scanned.
