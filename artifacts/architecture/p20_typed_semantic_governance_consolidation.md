# P20 — Typed semantic governance: consolidation as the official DBA layer

Consolidation only. No new benchmark, no new model calls, no new truthfulness
scores, no new heuristics. This fixes the *architecture* and *roles* that the
P16→P18→P19 sequence arrived at, marks the earlier stages as prerequisites (not
end states), and writes down the governance contract.

## A. Development path (how we got here)

| phase | what it established | status |
| ----- | ------------------- | ------ |
| **P16** | First REAL cross-model divergence (DeepSeek Alpha vs Granite Beta) on 5 claim-structural cases. Outcome: branch_required 4 / convergence 1; diffs missing_claim 6, extra_claim 2, relation_mismatch 2, granularity_mismatch 1. Showed independent builders **decompose the same answer differently** (e.g. tqa-0027 4-vs-2 claims). | **exploratory DBA prototype** |
| **P18** | Real embedding meaning-space (model2vec) over spl_core canonical candidates. Reduced branch_required 4→0 by recognising same-region reconstructions. BUT over-reduced: tqa-0007 falsely reconciled (a dropped negation scored cosine 0.871). | **semantic-alignment experiment** |
| **P19** | Typed logical-divergence governance: negation/polarity/quantifier/causal/temporal/modality/exclusivity checks can VETO a semantic reconciliation. Retracted the tqa-0007 false reconciliation (→ logical_polarity_conflict) while keeping the 4 legitimate granularity reconciliations. | **current recommended governance architecture** |

P16 and P18 are **necessary prerequisites**, not the end state: P16 proved
divergence is real (so DBA is worth doing), P18 proved a meaning-space is needed
(string diffs over-branch) AND proved it is unsafe alone (it merged a
contradiction). P19 is the first form that is both useful and safe.

## B. Why both naive forms are insufficient

- **Pure symbolic DBA** (P16): every granularity/grouping difference between two
  builders becomes missing_claim/extra_claim/relation_mismatch → near-universal
  `branch_required`. It cannot tell "different decomposition of the same fact"
  from "different fact". → **branch inflation**; the dual-builder signal is
  drowned in structural noise.
- **Pure embedding reconciliation** (P18): cosine region-similarity collapses
  granularity differences correctly, but is **negation/polarity/quantifier-blind**
  — it scored a dropped negation as same-region and merged a contradiction
  (tqa-0007). → **false reconciliation**; semantics silently overrides logic.

Symbolic-only over-branches; embedding-only under-branches on logical flips.
Neither is safe.

## C. The official form

```
semantic neighborhoods   (propose: same meaning-region?  — embedding, fast, recall-oriented)
        +
typed logical divergence governance   (veto: negation/polarity/quantifier/causal/temporal/modality/exclusivity)
        +
branching   (unresolved logical conflict -> keep both / branch, never merge, never vote)
```

Operating principle: **semantics may reconcile, logic may veto.** The
meaning-space is a fast same-region *prior*; the typed governance is the *guard*;
branching is the *safe default* when the guard fires or nothing reconciles. No
component ever selects a winner or estimates truth.

Governed outcomes (P19 `govern_outcome`): `semantic_reconcilable`,
`guarded_divergence`, `protected_branch_required`, `logical_polarity_conflict`
(plus pass-through `convergence` / `branch_required`).

## D. Four distinct ambiguity/relation kinds (do not conflate)

These were repeatedly confused across phases; the official architecture keeps
them separate, each with its own owner:

| kind | what it is | owner / mechanism | example |
| ---- | ---------- | ----------------- | ------- |
| **matcher ambiguity** | answer ties an answer-vs-gold matcher (string/overlap) | the **P12 exact-match tie resolver** (answer level), NOT DBA | tqa-0022 "No, I am your father." (1.00/1.00) |
| **reconstruction ambiguity** | two builders decompose the same region differently | meaning-space → `coarse_grain_equivalent` / `decomposition_variant` | tqa-0027 (4-vs-2 claims) |
| **logical polarity conflict** | same region BUT a negation/polarity/quantifier flip | typed governance → `logical_polarity_conflict` / `protected_branch_required` | tqa-0007 (dropped negation) |
| **semantic isomorphy** | two builders reconstruct the same claims | meaning-space → `reconstruction_isomorph` | tqa-0005 (region 0.999) |

The central P16→P19 lesson: matcher ambiguity is answer-level (not DBA's job);
reconstruction ambiguity is reconcilable; logical polarity conflict must branch;
semantic isomorphy is clean convergence. Collapsing any two of these is exactly
where the earlier stages erred.

## Status markers (authoritative)

- **P16 = exploratory DBA prototype** — proved real divergence; not a final scheme.
- **P18 = semantic alignment experiment** — proved the meaning-space helps and is
  unsafe alone; not to be deployed without the P19 guard.
- **P19 = current recommended governance architecture** — the layer DBA should
  use. Precision-sound; recall-limited (see the state report).

## Honesty (carried forward, not softened)

- Typed governance has **high precision** (what it flags — e.g. negation_flip —
  is real) but **unproven recall**: paraphrased negations, implicit
  quantifiers/causality, and subtle polarity flips can still slip through.
- The meaning-space is a **lightweight static embedding** (context-free); it
  captures coarse regions, not fine logical structure.
- **SPL-core itself remains primarily a gate / admissibility layer** — the
  meaning-space and governance sit *beside* it, not inside it; spl_core still has
  no learned meaning space.
- This document changes no code and runs no model; it records the architecture
  the prior phases earned.
