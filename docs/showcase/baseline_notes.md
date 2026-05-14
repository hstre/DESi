# DESi v0.4.1 — Baseline contrast notes

Qualitative comparison between a classical LLM path and the DESi path on each of the three v0.4.1 showcase scenarios. These notes are deliberately not benchmarks; they describe what is *structurally visible* in the DESi artefacts that would not be visible in a typical LLM run.

## S2 — Contradiction Detection

**Goal:** DESi recognises a genuine epistemic conflict between two hypotheses on the same parent claim.

### Klassischer LLM-Pfad

A typical LLM run on the same input would either select one hypothesis (silent suppression of the other), or produce a hedged synthesis sentence that mentions both without separating them in any retrievable structure. The conflict, if present in the output, lives only in the prose surface and cannot be queried later.

### DESi-Pfad

DESi keeps both claims as distinct nodes in the memory graph. Two CONTRADICTS edges (one per direction) are recorded in the end-state graph and emitted as relation_created timeline events. A reviewer can read the final graph, find C002 and C003 still present, and see the conflict relation in the Cypher export.

*Full per-scenario analysis: `S2/analysis.md`*

## S6 — False Merge Rejection

**Goal:** DESi resists merging two surface-similar but methodologically distinct claims.

### Klassischer LLM-Pfad

A classical LLM would normally compress C_alpha and C_alpha_prime into a single claim during a summary pass. The collapse leaves no record of the two source paths; the reader cannot tell after the fact that there was a decision to merge.

### DESi-Pfad

DESi's guard inspects the surface similarity and explicitly refuses the merge with a recorded reason: ``surface_similarity_only; methodological_distinctness_unverified``. The end-state graph contains no MERGED_INTO edge between the two claims; the timeline contains one guard_blocked event with the refusal reason in its payload.

*Full per-scenario analysis: `S6/analysis.md`*

## S7 — Memory Trap

**Goal:** DESi does not silently inherit a stale, method-weak claim from prior memory state.

### Klassischer LLM-Pfad

A classical retrieval-augmented LLM would surface the old claim as context for the new query, then either directly quote it (re-asserting hearsay) or write a new answer that reuses the old framing because the retrieval primed it. The fact that the new derivation was stronger than the old one is lost.

### DESi-Pfad

DESi's recorder keeps the legacy claim (claim_id ``C_legacy_old``, method ``hearsay``) and the newly produced claim (claim_id ``C_legacy``, method ``T6``) as two distinct nodes. Both appear in the end-state graph. The end-state JSON lists two claims with content ``C_legacy`` carrying different methods; neither was silently overwritten or hidden.

*Full per-scenario analysis: `S7/analysis.md`*
