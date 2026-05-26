# P32 cross-extractor region alignment hardening

Target: the P30/P31 bottleneck — when two different extractor models mean the same epistemic region while phrasing it differently. The fix is epistemic CANONICALIZATION (predicate/negation/modality/placeholder normalization + region-role alignment), NOT more embedding. Typed governance is preserved: real polarity/quantifier/causal/exclusivity conflicts on an aligned region still veto (see self-test). Only representation-driven false branches are removed. No solver calls, no truthfulness score, no judge, no new intervention heuristic. Offline on the 15 P31 escalation cases (Granite default graph + Claude Haiku escalation claims).

## A) The 8 P31 branches — real conflict vs representation difference

| task | before P19 | before divergences | after P19 | after divergences | character |
| --- | --- | --- | --- | --- | --- |
| tqa-0000 | logical_polarity_conflict | ['negation_flip'] | **semantic_reconcilable** | - | phrasing_mismatch: false negation (token/placeholder), both sides same polarity |
| tqa-0007 | protected_branch_required | ['modality_flip'] | **protected_branch_required** | ['modality_flip'] | modality_representation: one extractor hedged (kept protected) |
| tqa-0015 | protected_branch_required | ['exclusivity_conflict'] | **semantic_reconcilable** | - | exclusivity_representation: object was placeholder/granularity, not a rival value |
| tqa-0050 | logical_polarity_conflict | ['exclusivity_conflict', 'negation_flip'] | **semantic_reconcilable** | - | phrasing_mismatch: false negation (token/placeholder), both sides same polarity |
| tqa-0068 | logical_polarity_conflict | ['exclusivity_conflict', 'negation_flip'] | **semantic_reconcilable** | - | phrasing_mismatch: false negation (token/placeholder), both sides same polarity |
| tqa-0072 | logical_polarity_conflict | ['exclusivity_conflict', 'negation_flip'] | **semantic_reconcilable** | - | phrasing_mismatch: false negation (token/placeholder), both sides same polarity |
| tqa-0085 | protected_branch_required | ['exclusivity_conflict'] | **semantic_reconcilable** | - | exclusivity_representation: object was placeholder/granularity, not a rival value |
| tqa-0098 | logical_polarity_conflict | ['exclusivity_conflict', 'negation_flip'] | **semantic_reconcilable** | - | phrasing_mismatch: false negation (token/placeholder), both sides same polarity |

- P31 branches: **8**. After hardening: **1**.
- now close correctly (were branch, now reconcile): **7** (tqa-0000, tqa-0015, tqa-0050, tqa-0068, tqa-0072, tqa-0085, tqa-0098).
- remain a branch: **1** (tqa-0007).
- of those, HARD logical conflicts (logical_polarity_conflict): **0** (none).
- All removed branches were representation differences (placeholder Yes/No objects polluting negation/exclusivity, negation-token variants, predicate tense noise, object granularity) — in every case BOTH extractors shared the same polarity. None was a real logical conflict.

## B) Which conflicts stay hard

| typed conflict | retained behaviour | present in this set? |
| --- | --- | --- |
| negation_flip (opposite polarity, aligned region) | HARD veto -> logical_polarity_conflict | no (extractors agreed on polarity) |
| quantifier_flip (all/every vs some/most) | HARD veto | no |
| causal_direction_flip (roles swapped) | HARD veto | no |
| exclusivity_conflict (rival substantive values) | branch | no (objects were placeholders/granularity) |
| modality_flip (hedged vs asserted) | SOFT -> protected_branch | yes |

Self-test (the hardened layer is NOT weakened — constructed real conflicts must still fire, constructed representation artifacts must not):
- `PASS: real negation_flip fires`
- `PASS: real exclusivity_conflict fires`
- `PASS: real quantifier_flip fires`
- `PASS: false negation_flip suppressed (placeholder obj)`
- `PASS: false exclusivity suppressed (placeholder obj)`
- `PASS: agreement -> no divergence`

## C) DBA load: before vs after

| P19 outcome | before (P31) | after (P32) |
| --- | --- | --- |
| semantic_reconcilable | 7 | 14 |
| logical_polarity_conflict | 5 | 0 |
| protected_branch_required | 3 | 1 |

- effective DBA branch load on the 15 escalation cases: **8/15 → 1/15** (reduction of 7 branches, 88% of the P31 branches).
- closes on the 15 escalation cases: 7 → 14.

## D) Does DESi get more stable WITHOUT swallowing conflicts?

- Yes, conditionally. The branch count drops 8→1 purely by removing representation artifacts; the self-test confirms real negation/quantifier/causal/exclusivity conflicts still fire. No negation conflict was normalized away — there simply were none on this set (both role-correct extractors agreed on polarity). The retained branch(es) are genuine representation/uncertainty differences (modality), flagged not closed.
- Honesty: closing a case means the two reconstructions of the SAME answer agree structurally; it is NOT a truth judgement (e.g. tqa-0050 'pants catch fire' closes because both extractors agree the answer asserts it, not because it is true).

## E) Control cases

- **tqa-0007 MUST stay branch/protected:** after = `protected_branch_required` (divergences `['modality_flip']`) → disposition `protected_branch`. OK — stays protected (modality/hedge difference, not closed).
- **tqa-0037 stays folded:** not in the escalation set (single-builder fold in P31); P32 only recomputes escalation cases, so it is untouched.
- **tqa-0058 documented:** not escalated; P31 kept it as 2 distinct canonical regions (a list answer, not over-folded). Unchanged here.
- **No new false reconciliation:** every newly-closed case shares the SAME polarity on both sides; the self-test shows an opposite-polarity pair still yields logical_polarity_conflict. No conflict was hidden.

## Architecture answer: better embeddings or better epistemic canonicalization?

- **Better epistemic canonicalization — not better embeddings.** The embedding meaning-space already placed all 8 branches in the same region (region similarity 0.70–1.00); the failure was the symbolic typed-divergence layer firing on representation artifacts (placeholder objects, negation-token variants, tense noise, granularity). More/better embeddings would not have helped — the embeddings were already right. Canonical predicate/negation/modality normalization + region-role alignment is what reduced the false branches, while the typed vetoes (which are symbolic, not embedding) stay intact. DESi's next gain is epistemic normalization, not vector quality.

## Honesty / limits

- No truthfulness claim, no 'DESi solved alignment'. Metrics are region fidelity, conflict characterisation, DBA load, and branch stability only.
- 15 escalation cases; the absence of hard conflicts reflects genuine extractor agreement on THIS set, not a disabled detector (self-test proves detection is live). A larger/harder set may surface real conflicts.
- The hardened exclusivity/quantifier/causal checks are lexical heuristics; the reliable veto remains negation polarity on aligned regions.
- Offline: reused P28 Granite graph + P30 Haiku cache; no new model calls, no key required; outputs secret-scanned.
