# SPL meaning-space alignment report (P18)

Real embedding meaning-space (model2vec static embeddings) layered on spl_core canonical candidates, used to re-characterise P16 granularity/grouping-only `branch_required` as same-region meaning alignment. No judge, no vote, no truth decision.

- embedding backend available: **True** (model2vec minishlab/potion-base-8M).
- Gβ (Granite) source: no persisted Gβ and no OPENROUTER_API_KEY.

## Real Gβ unavailable — embedding mechanism validated offline

No persisted Gβ and no key, so the real DeepSeek-vs-Granite reduction is NOT computed (no reduction claimed). The real embedding meaning-space is instead validated on the Alpha graphs with REAL embeddings:

| task | nα | self (identity) | coarse-merge variant | cross-case (other task) | region(self/merge/cross) |
| --- | --- | --- | --- | --- | --- |
| tqa-0005 | 3 | reconstruction_isomorph | reconstruction_isomorph | unresolved_semantic_divergence | 1.0/1.0/0.122 |
| tqa-0007 | 4 | reconstruction_isomorph | coarse_grain_equivalent | unresolved_semantic_divergence | 1.0/0.807/0.123 |
| tqa-0018 | 2 | reconstruction_isomorph | coarse_grain_equivalent | unresolved_semantic_divergence | 1.0/0.777/0.108 |
| tqa-0027 | 4 | reconstruction_isomorph | coarse_grain_equivalent | unresolved_semantic_divergence | 1.0/0.835/0.022 |
| tqa-0080 | 2 | reconstruction_isomorph | coarse_grain_equivalent | unresolved_semantic_divergence | 1.0/0.704/0.047 |

- identity -> reconstruction_isomorph: PASS.
- coarser merge of same region -> reconcilable (coarse_grain/decomposition): PASS.
- different task's claims -> unresolved_semantic_divergence: PASS — the embedding space separates different meaning regions (high region sim within, low across).
- This validates the embedding meaning-space distinguishes same-region vs different-region with REAL embeddings (not lexical). The real Gα/Gβ branch_required reduction needs one Granite re-run (provide OPENROUTER_API_KEY and re-run; Gβ is then persisted to `p18_granite_builder_graphs.limit100.jsonl`).

## Architecture question: is SPL now a semantic reconstruction space?

- **No — spl_core itself is still only a gate.** The meaning-space is a SEPARATE embedding layer (model2vec) bolted onto spl_core's canonical candidates; spl_core's own projection remains a confidence-shaped entropy with no embedding. So 'SPL' (the admissibility core) is unchanged; DBA now has a real semantic neighborhood layer *beside* it.
- **But DBA now does have a real meaning-space:** alignment is cosine in a trained (distilled) embedding space, which genuinely captures paraphrase and region equivalence that lexical overlap missed (P17). That is the real advance.
- **Remaining limits / next architecture step:** model2vec is a LIGHT static embedding (no context, no torch); it captures coarse semantic regions, not fine logical/quantifier/temporal distinctions. The next limit is that region-similarity can call two claims same-region while a critical negation/quantifier flips meaning — so a meaning-space cannot replace the typed diff engine; it should gate it. A contextual embedding or a real relation/ontology layer is the next step.

## Honesty / limits

- model2vec static embeddings are a REAL but LIGHTWEIGHT meaning-space (distilled, context-free). semantic similarity != truth and != logical equivalence; negation/quantifier flips can be missed.
- Reused spl_core (no new parallel SPL). The only model calls are an optional Granite re-run of the 5 P16 cases. No judge/vote/aggregation, no truthfulness scores, no intervention/SPL-core changes.
- No real DeepSeek-vs-Granite reduction was computed in this run; the synthetic/offline validation is NOT presented as the real result.
