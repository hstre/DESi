# SPL meaning-space alignment report (P18)

Real embedding meaning-space (model2vec static embeddings) layered on spl_core canonical candidates, used to re-characterise P16 granularity/grouping-only `branch_required` as same-region meaning alignment. No judge, no vote, no truth decision.

- embedding backend available: **True** (model2vec minishlab/potion-base-8M).
- Gβ (Granite) source: persisted p18 artifact.

## Real reduction (P16 -> P18, DeepSeek vs Granite)

- branch_required: **4 -> 0** (reduced by 4).
- P16 outcomes: `{'branch_required': 4, 'convergence': 1}` ; P18 outcomes: `{'reconstruction_isomorph': 1, 'decomposition_variant': 1, 'convergence': 1, 'coarse_grain_equivalent': 2}`

| task | nα | nβ | P16 | meaning alignment | region sim | P18 |
| --- | --- | --- | --- | --- | --- | --- |
| tqa-0005 | 3 | 3 | branch_required | reconstruction_isomorph | 0.999 | **reconstruction_isomorph** |
| tqa-0007 | 4 | 4 | branch_required | decomposition_variant | 0.871 | **decomposition_variant** |
| tqa-0018 | 2 | 2 | convergence | reconstruction_isomorph | 1.0 | **convergence** |
| tqa-0027 | 4 | 2 | branch_required | coarse_grain_equivalent | 0.786 | **coarse_grain_equivalent** |
| tqa-0080 | 2 | 1 | branch_required | coarse_grain_equivalent | 0.697 | **coarse_grain_equivalent** |

## Core analysis cases

- `tqa-0027`: P16 branch_required -> P18 **coarse_grain_equivalent** (alignment coarse_grain_equivalent, region 0.786, diffs {'missing_claim': 4, 'extra_claim': 2}).
- `tqa-0080`: P16 branch_required -> P18 **coarse_grain_equivalent** (alignment coarse_grain_equivalent, region 0.697, diffs {'missing_claim': 1}).
- `tqa-0007`: P16 branch_required -> P18 **decomposition_variant** (alignment decomposition_variant, region 0.871, diffs {'missing_claim': 1, 'granularity_mismatch': 1, 'relation_mismatch': 1}).

## Was relation_mismatch mostly a decomposition variant?

- relation_mismatch-only cases and their meaning alignment: tqa-0005=reconstruction_isomorph. Where the region matches, relation_mismatch was a decomposition/grouping artefact, not real divergence.

## OVER-REDUCTION AUDIT (honesty-critical)

- **1 case(s) were reconciled DESPITE a negation divergence the embedding missed** — a likely FALSE reconciliation:
  - `tqa-0007`: region 0.871 -> `decomposition_variant`, but one builder carries a negation the other dropped (meaning flip). e.g. tqa-0007: Alpha 'would NOT penetrate the skin' / 'NOT cause serious injury' vs Granite 'penetrate skin' / 'cause serious injury'. Static embeddings score these as same-region (high cosine) but they are CONTRADICTORY. This is NOT a safe reconciliation.
- **Therefore the 4->0 reduction is NOT a clean win.** At least 1 of the reductions is a false same-region call caused by the embedding's negation-blindness.

## Reading (honest)

- **branch_required reduced 4 -> 0** on these cases — but see the over-reduction audit: the embedding meaning-space genuinely reconciles granularity/grouping (tqa-0027 coarse_grain, tqa-0005 isomorph) AND over-reconciles a negation flip (tqa-0007). So the raw count overstates the safe reduction.
- **Did the embedding help beyond lexical?** Yes for granularity: it scores differently-decomposed same-region reconstructions as same-region where token overlap would not (tqa-0027 region 0.79 with 2-vs-4 claims). **But it is negation/quantifier-blind**, so it must GATE the typed diff engine, never replace it.
- **Net:** the meaning-space is a real, useful neighbourhood signal for granularity/decomposition, and a DANGEROUS one for logical flips. Safe use = reconcile only when the typed diff engine shows no negation/quantifier/causality mismatch.

## Architecture question: is SPL now a semantic reconstruction space?

- **No — spl_core itself is still only a gate.** The meaning-space is a SEPARATE embedding layer (model2vec) bolted onto spl_core's canonical candidates; spl_core's own projection remains a confidence-shaped entropy with no embedding. So 'SPL' (the admissibility core) is unchanged; DBA now has a real semantic neighborhood layer *beside* it.
- **But DBA now does have a real meaning-space:** alignment is cosine in a trained (distilled) embedding space, which genuinely captures paraphrase and region equivalence that lexical overlap missed (P17). That is the real advance.
- **Remaining limits / next architecture step:** model2vec is a LIGHT static embedding (no context, no torch); it captures coarse semantic regions, not fine logical/quantifier/temporal distinctions. The next limit is that region-similarity can call two claims same-region while a critical negation/quantifier flips meaning — so a meaning-space cannot replace the typed diff engine; it should gate it. A contextual embedding or a real relation/ontology layer is the next step.

## Honesty / limits

- model2vec static embeddings are a REAL but LIGHTWEIGHT meaning-space (distilled, context-free). semantic similarity != truth and != logical equivalence; negation/quantifier flips can be missed.
- Reused spl_core (no new parallel SPL). The only model calls are an optional Granite re-run of the 5 P16 cases. No judge/vote/aggregation, no truthfulness scores, no intervention/SPL-core changes.
