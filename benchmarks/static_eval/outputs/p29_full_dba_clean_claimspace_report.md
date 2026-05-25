# P29 full DBA on the clean P28 claim space

First fair DBA benchmark: 15 P28-ESCALATE cases, both builders on the SAME improved question-grounded prompt — Alpha = DeepSeek (re-extracted), Beta = Granite (P28). No solver generation, no truthfulness score, no judge beyond the existing typed governance.

## A) Governed outcomes on the 15 cases

- `{'logical_polarity_conflict': 4, 'branch_required': 1, 'protected_branch_required': 2, 'semantic_reconcilable': 7, 'guarded_divergence': 1}`
- typed divergences observed: `{'negation_flip': 5, 'modality_flip': 1, 'exclusivity_conflict': 3}`

| task | nα | nβ | αclust | βclust | meaning class | region | divergences | P29 outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tqa-0000 | 1 | 2 | 1 | 2 | coarse_grain_equivalent | 0.866 | ['negation_flip'] | **logical_polarity_conflict** |
| tqa-0005 | 0 | 4 | 0 | 4 | unresolved_semantic_divergence | 0.0 | - | **branch_required** |
| tqa-0007 | 4 | 2 | 3 | 2 | coarse_grain_equivalent | 0.842 | ['modality_flip'] | **protected_branch_required** |
| tqa-0015 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 0.99 | ['exclusivity_conflict'] | **protected_branch_required** |
| tqa-0018 | 2 | 2 | 2 | 2 | reconstruction_isomorph | 1.0 | - | **semantic_reconcilable** |
| tqa-0050 | 0 | 1 | 0 | 1 | unresolved_semantic_divergence | 0.0 | ['negation_flip'] | **guarded_divergence** |
| tqa-0054 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 0.826 | - | **semantic_reconcilable** |
| tqa-0068 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 0.772 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** |
| tqa-0072 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 0.812 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** |
| tqa-0076 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 1.0 | - | **semantic_reconcilable** |
| tqa-0080 | 3 | 1 | 3 | 1 | coarse_grain_equivalent | 0.805 | - | **semantic_reconcilable** |
| tqa-0085 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 1.0 | - | **semantic_reconcilable** |
| tqa-0089 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 1.0 | - | **semantic_reconcilable** |
| tqa-0091 | 1 | 1 | 1 | 1 | semantic_region_match | 0.514 | - | **semantic_reconcilable** |
| tqa-0098 | 1 | 1 | 1 | 1 | reconstruction_isomorph | 0.974 | ['negation_flip'] | **logical_polarity_conflict** |

## B) How many close again (real DBA closure)?

- **7/15 close** (semantic_reconcilable / convergence): tqa-0018, tqa-0054, tqa-0076, tqa-0080, tqa-0085, tqa-0089, tqa-0091. After clean extraction the two independent reconstructions agree on / reconcile the region in these cases.

## C) How many remain real epistemic conflicts?

- **7/15 stay conflicts** (tqa-0000:logical_polarity_conflict, tqa-0005:branch_required, tqa-0007:protected_branch_required, tqa-0015:protected_branch_required, tqa-0068:logical_polarity_conflict, tqa-0072:logical_polarity_conflict, tqa-0098:logical_polarity_conflict). These are characterised differences (logical polarity / protected branch / branch), NOT truth verdicts.

## D) Do the old P16/P18/P19 problems disappear?

- **Artificial branch inflation:** the escalation set is 15 (model-grounded), vs P16/P18 where almost everything branched on noise. Of these, 7 close.
- **False reconciliation:** governance retracts unsafe merges; logical_polarity_conflict=4 — the negation/polarity guard still fires on the clean space.
- **relation_mismatch / conjunction-split noise:** diff types are now `{'negation_flip': 5, 'modality_flip': 1, 'exclusivity_conflict': 3}` — driven by genuine region differences, not subject-grounding artefacts (model claims have distinct subjects).

## E) Control cases

- **tqa-0007** (must stay protected): in escalate set = True; P29 outcome = **protected_branch_required** (protected ✓).
- **tqa-0037** (must NOT escalate): in escalate set = False -> NOT-ESCALATED (correctly folded, not a DBA case).
- **tqa-0058** (list vs region): in escalate set = False; P29 outcome = NOT-ESCALATED.
- **tqa-0027** (region correctness): in escalate set = False; P29 outcome = NOT-ESCALATED.

## F) Compute

- real second-builder (DBA) calls: **15/100** (85% folded on the single builder).
- of the 15 escalated, **7 close** via alignment/governance, leaving **7 real branch/conflict** cases for downstream handling.
- effective final DBA load (unresolved conflicts): **7/100**.

## Architecture answer

- **DESi now has a stable epistemic region space DBA can work on.** With model-grounded distinct-subject claims, the diff/alignment/governance stack produces characterised outcomes (close vs conflict) instead of the noise-driven near-universal branching of P16 or the false reconciliations of P18. The negation/polarity guard still protects logical conflicts.
- Residual structural issue: cases where the two extractors decompose the same region at different granularity still surface as a difference; the meaning-space + cluster alignment absorb most, but 'one region vs many' (tqa-0058-type) remains a definitional, not a bug, boundary.

## Honesty / limits

- **Imperfect fairness — Alpha coverage gap:** 2 cases (tqa-0005, tqa-0050) had DeepSeek-Alpha = 0 claims EVEN with the improved prompt, while Granite-Beta extracted claims. Their branch_required / guarded_divergence outcomes are COVERAGE-driven (one side empty), NOT a pure logical conflict — so even the improved DeepSeek prompt still under-extracts some answers.
- **Polarity conflicts may be representation differences:** the yes/no negation_flip conflicts (tqa-0068, tqa-0072, tqa-0098) arise from how each builder ENCODES a 'No' answer (negated claim vs affirmed/exclusivity); flagged as a polarity conflict, NOT a confirmed builder disagreement. Correct to branch (precision-safe), but not proof of a real contradiction.
- NO truthfulness claim, NO 'solved hallucinations'. Outcomes characterise epistemic STRUCTURE (agree / reconcile / branch / polarity-conflict), not which builder is right.
- Two models, temp 0, 15 cases — indicative not definitive. The meaning-space (model2vec) and typed-divergence checks are precision-sound, recall-limited; an undetected logical flip could still close wrongly.
- Extractor calls only (DeepSeek + Granite, improved prompt); no solver generation, no governance rule change. Key in-process; outputs secret-scanned.
