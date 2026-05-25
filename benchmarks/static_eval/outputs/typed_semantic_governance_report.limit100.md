# Typed semantic governance report (P19)

Governance layer between the embedding meaning-space (P18) and DBA adjudication. Principle: **semantics may reconcile, logic may veto.** A same-region reconciliation is blocked when a typed LOGICAL divergence (negation/polarity/quantifier/causal/temporal/modality/exclusivity) is detected. Offline on persisted P18 Gβ; no model calls, no judge, no vote, no truth decision.

## P18 reconciliation vs P19 governed outcome

| task | nα | nβ | meaning class | region | P18 outcome | typed divergences | P19 outcome | retracted? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tqa-0005 | 3 | 3 | reconstruction_isomorph | 0.999 | reconstruction_isomorph | - | **semantic_reconcilable** | - |
| tqa-0007 | 4 | 4 | decomposition_variant | 0.871 | decomposition_variant | ['exclusivity_conflict', 'modality_flip', 'negation_flip'] | **logical_polarity_conflict** | YES |
| tqa-0018 | 2 | 2 | reconstruction_isomorph | 1.0 | convergence | - | **semantic_reconcilable** | - |
| tqa-0027 | 4 | 2 | coarse_grain_equivalent | 0.786 | coarse_grain_equivalent | - | **semantic_reconcilable** | - |
| tqa-0080 | 2 | 1 | coarse_grain_equivalent | 0.697 | coarse_grain_equivalent | - | **semantic_reconcilable** | - |

- **false reconciliations prevented (retracted): 1** (tqa-0007).
- still semantic_reconcilable: ['tqa-0005', 'tqa-0018', 'tqa-0027', 'tqa-0080'].
- protected (branch/conflict): ['tqa-0007'].
- P18 outcomes: `{'reconstruction_isomorph': 1, 'decomposition_variant': 1, 'convergence': 1, 'coarse_grain_equivalent': 2}` ; P19 outcomes: `{'semantic_reconcilable': 4, 'logical_polarity_conflict': 1}`
- typed divergences observed: `{'exclusivity_conflict': 1, 'modality_flip': 1, 'negation_flip': 1}`

## Core case: tqa-0007 — why P18 reconciled wrongly, and the P19 fix

- P18 called it **decomposition_variant** (meaning class decomposition_variant, region 0.871) — high cosine because the static embedding ignores the dropped negation.
- P19 typed divergences: `['exclusivity_conflict', 'modality_flip', 'negation_flip']` -> governed outcome **logical_polarity_conflict**. The negation_flip is a HARD logic veto, so the semantic reconciliation is retracted: Alpha 'would NOT penetrate the skin' / 'NOT cause serious injury' vs Granite 'penetrate skin' / 'cause serious injury' are CONTRADICTORY and must not be merged on cosine similarity.

## Reading

- **False reconciliation reduced?** Yes: 1 P18 reconciliation(s) retracted by a logic veto; the legitimate granularity/decomposition reconciliations are kept (semantic_reconcilable).
- **Is branch_required now epistemically more sensible?** Yes — branching is now driven by LOGICAL conflict (protected_branch_required / logical_polarity_conflict), not by surface granularity. Granularity differences reconcile; polarity/negation differences branch. That is the intended split.
- **Most important typed divergence here:** negation_flip (caught tqa-0007). The others (quantifier/causal/temporal/polarity/exclusivity) did not fire on these 5 cases — so their value is unproven here.
- **Is the meaning-space now safely embedded?** Safer: it can only reconcile when the typed logic checks pass. The remaining risk is the checks' RECALL — they are lexical/embedding heuristics, so a logical flip they don't detect could still slip through (see limits).

## Architecture question

- **Yes — the right form is: semantic neighborhoods + typed divergence governance + branching, NOT pure embedding reconciliation.** P18 proved pure embedding reconciliation is unsafe (it merged a contradiction). P19 shows the safe composition: the meaning-space proposes reconciliation, a typed logical layer can veto it, and unresolved logical conflict branches. Semantics is a fast same-region prior; logic is the guard.

## Honesty / limits

- The typed divergence checks are **lexical / small-lexicon / embedding heuristics**, not a trained NLI model. negation_flip is reliable here; the others have unproven recall and WILL miss flips outside their patterns (e.g. paraphrased negation, implicit quantifiers, subtle causal reversal). So 'logic may veto' currently has limited recall — false reconciliations can still occur for undetected flips.
- No new Granite calls (persisted P18 Gβ). spl_core reused. No judge, no vote, no aggregation, no truthfulness scores, no intervention/SPL-core changes.
- **Next architecture limit:** the veto layer needs higher-recall logical divergence detection (a real NLI / entailment-polarity model), and the exclusivity check needs better cross-model claim alignment. Until then the guard is sound in PRECISION (what it flags is real) but weak in RECALL.
