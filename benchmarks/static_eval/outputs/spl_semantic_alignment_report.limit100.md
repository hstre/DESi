# SPL semantic alignment report (P17)

Cross-model claim alignment via spl_core, applied to the P16 DeepSeek(Alpha)-vs-Granite(Beta) cases, to re-characterise granularity/grouping-only `branch_required` as same-region alignment. No judge, no vote, no truth decision. Alignment is canonical-lexical + spl_core projection signals — NOT a learned meaning embedding (see scope note).

Gβ source: no persisted Gβ and no OPENROUTER_API_KEY (Granite re-run not possible).

## Builder Beta unavailable — mechanism validation only

No persisted Gβ and no key, so the real DeepSeek-vs-Granite reduction is NOT computed here (the P16 Granite claims were not persisted; one Granite re-run is needed). **No reduction is claimed.** Instead the alignment MECHANISM is unit-tested offline on the Alpha graphs:

| task | n_alpha | Alpha-self alignment | granularity-variant alignment | reconcilable |
| --- | --- | --- | --- | --- |
| tqa-0005 | 3 | semantic_isomorph | semantic_isomorph | True |
| tqa-0007 | 4 | semantic_isomorph | granularity_overlap | True |
| tqa-0018 | 2 | semantic_isomorph | granularity_overlap | True |
| tqa-0027 | 4 | semantic_isomorph | granularity_overlap | True |
| tqa-0080 | 2 | semantic_isomorph | granularity_overlap | True |

- Alpha-vs-Alpha => semantic_isomorph for all: PASS (identity must be isomorphic).
- Known granularity difference (claims merged into a coarser same-region reconstruction) classified as a reconcilable `granularity_overlap`, NOT `structurally_divergent`, for every multi-subject-collapsing case: PASS (cases whose claims have distinct subjects stay semantic_isomorph, which is also correct). This is a UNIT TEST of the mechanism, NOT a claim about real model divergence.
- To get the real reduction: provide OPENROUTER_API_KEY and re-run (Granite re-runs the 5 cases, Gβ is persisted, real alignment applied).

## Architecture question: was SPL admissibility or semantic alignment?

- **SPL has been an ADMISSIBILITY / entropy layer, not a semantic alignment layer.** `spl_core` projects a claim into a confidence-shaped entropy over a SYNTHETIC relation distribution (keyed on the predicate string) and gates it (E0–E3). That is excellent for 'should this claim be admitted?', but it carries **no meaning-space / embedding**, so it cannot natively tell that two differently-worded claims denote the same fact.
- P17's alignment therefore leans on the CANONICAL form (normalised s/p/o token overlap) plus spl_core's projection/entropy *neighbourhood* as a secondary signal. It recognises lexical/structural isomorphism and region overlap — a real, useful step — but it is NOT semantic understanding and isomorphy is NOT 'solved'.
- **Architecture limit now visible:** to be a true semantic alignment layer, SPL needs a genuine meaning space (embeddings or a real relation matrix), not a confidence-derived entropy. Until then, cross-model alignment is bounded by lexical/canonical overlap of the extracted claims.

## Honesty / limits

- Alignment is canonical-lexical + spl_core projection signals, NOT a learned embedding; semantic_isomorph here = lexical/structural isomorphism, not proven meaning-equivalence.
- Reused spl_core (no new parallel SPL). No new API calls beyond an optional Granite re-run of the 5 P16 cases. No judge/vote/aggregation, no new truthfulness scores, no intervention/SPL-core changes.
