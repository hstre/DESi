# P31 full-100 role-correct DESi run

First complete DESi pass with the P30 role architecture: existing P12 live answers as solver output; IBM Granite as the always-on DEFAULT extractor (existing P28 full-100 graph); Claude Haiku 4.5 as the ESCALATION second builder (P30 cache); SPL meaning-space + P19 typed governance for adjudication; P26/P28 folding. No DeepSeek in the standard path, no new solver calls, no truthfulness score, no judge, no majority vote, no new intervention heuristics. Structural / compute metrics only.

Granite extracts all 100; P21/P26 escalate 15; only the escalated minority reaches DBA. All escalation Haiku claims were served from the P30 cache (0 new live calls in this run).

## A) Full-100 architecture metrics

| metric | value |
| --- | --- |
| cases (full set) | 100 |
| Granite claim coverage: cases with ≥1 claim | 72/100 |
| empty answers (0 claims; all UNKNOWN/refusal) | 28/100 |
| substantive answers with 0 claims (coverage gap) | 0 |
| total Granite claims | 100 (mean 1.39/covered case) |
| canonical clusters (total) | 90 (mean 1.25/covered case) |
| folded / closed (single-builder, ≥1 claim, not escalated) | 57 |
| empty (no DBA, no claims) | 28 |
| escalated (-> DBA) | 15 |
| Claude second-extractor calls | 15 (all from P30 cache; 0 new live calls) |
| DBA: semantic_reconcilable | 7 |
| DBA: convergence | 0 |
| DBA: protected_branch_required | 3 |
| DBA: logical_polarity_conflict | 5 |
| DBA: unresolved_divergence (branch_required + guarded_divergence) | 0 |
| DBA: coverage_asymmetry (extractor_failure) | 0 |
| **final effective DBA load** | **15/100 = 15%** |
| of which close (reconcile/converge) | 7 |
| of which real branch (protected/conflict/unresolved) | 8 |

Per-escalated-case DBA outcomes:

| task | nα (Granite) | nβ (Claude) | meaning class | region | typed divergences | P19 outcome | disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tqa-0000 | 2 | 2 | reconstruction_isomorph | 0.90 | ['negation_flip'] | **logical_polarity_conflict** | protected_branch |
| tqa-0005 | 4 | 3 | coarse_grain_equivalent | 0.86 | - | **semantic_reconcilable** | close |
| tqa-0007 | 2 | 4 | coarse_grain_equivalent | 0.85 | ['modality_flip'] | **protected_branch_required** | protected_branch |
| tqa-0015 | 1 | 1 | reconstruction_isomorph | 0.95 | ['exclusivity_conflict'] | **protected_branch_required** | protected_branch |
| tqa-0018 | 2 | 2 | reconstruction_isomorph | 1.00 | - | **semantic_reconcilable** | close |
| tqa-0050 | 1 | 1 | decomposition_variant | 0.70 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** | protected_branch |
| tqa-0054 | 1 | 1 | reconstruction_isomorph | 0.81 | - | **semantic_reconcilable** | close |
| tqa-0068 | 1 | 1 | reconstruction_isomorph | 0.77 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** | protected_branch |
| tqa-0072 | 1 | 1 | reconstruction_isomorph | 0.81 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** | protected_branch |
| tqa-0076 | 1 | 1 | reconstruction_isomorph | 1.00 | - | **semantic_reconcilable** | close |
| tqa-0080 | 1 | 2 | semantic_region_match | 0.45 | - | **semantic_reconcilable** | close |
| tqa-0085 | 1 | 1 | reconstruction_isomorph | 0.92 | ['exclusivity_conflict'] | **protected_branch_required** | protected_branch |
| tqa-0089 | 1 | 1 | reconstruction_isomorph | 1.00 | - | **semantic_reconcilable** | close |
| tqa-0091 | 1 | 1 | semantic_region_match | 0.51 | - | **semantic_reconcilable** | close |
| tqa-0098 | 1 | 1 | reconstruction_isomorph | 0.91 | ['exclusivity_conflict', 'negation_flip'] | **logical_polarity_conflict** | protected_branch |

## B) Compute

Estimates use P30 per-extraction mean tokens × OpenRouter list pricing; the escalation Claude cost is the ACTUAL cached token count. P30 means come from the hard 17-case subset, so full-100 estimates are a conservative upper bound (easy answers are shorter).

| line | value |
| --- | --- |
| Granite default extraction (100) — estimated | $0.0020 ($0.020/1000) |
| Claude escalation extraction (15) — ACTUAL tokens 4681/1817 | $0.0138 |
| **role-correct total (Granite×100 + Claude×15)** | **$0.0158** |
| always-dual-builder (Granite×100 + Claude×100) — estimated | $0.0998 |
| DeepSeek-as-extractor (×100, single) — estimated | $0.0742 |
| **saving vs always-dual-builder** | **$0.0840 (84%)** |

Output-token comparison (mean tokens/extraction, P30): Granite 58, Claude Haiku 133, DeepSeek 712 (DeepSeek ≈ 12× Granite output).

Real savings: routing escalation to Claude only on the 15/100 escalated cases (not all 100) avoids 85 Claude extractions ≈ $0.0831, an 84% reduction vs always-dual-builder, while keeping the common path at Granite cost. A DeepSeek-as-extractor pipeline would cost ≈ $0.0742 (~5× the role-correct pipeline) for worse, less stable extraction. Savings are extractor-layer estimates, not a pipeline-wide claim.

## C) Control cases

- **tqa-0007 protected?** escalated=True → P19 `protected_branch_required` (divergences `['modality_flip']`, disposition `protected_branch`). Still a protected branch / logical veto.
- **tqa-0037 folded?** escalated=False → 1 Granite claims → 1 cluster(s), disposition `folded_single_builder` (single-builder fold, no DBA).
- **tqa-0058 list/region?** escalated=False → 4 Granite claims → 2 canonical region(s), disposition `folded_single_builder` (list answer kept as distinct regions, not over-folded).
- **tqa-0027 stable?** escalated=False → 1 Granite claims → 1 cluster(s), disposition `folded_single_builder` (stable single-builder).

## D) Architecture answer

- Does DESi now have a role-correct, compute-efficient, epistemically stable full-100 path? **Largely yes, with one honest caveat.** The pipeline runs end-to-end with clean role separation: Granite extracts all 100 cheaply (≥1 claim on all 72 substantive answers, 28 empty UNKNOWN/refusal answers, 0 substantive coverage gaps), P21/P26 escalate only 15 (15%), and Claude Haiku acts as an independent second builder only there. The 100 cases split into 57 folded single-builder + 28 empty + 15 escalated. DBA load is bounded to the escalated minority; 7 close and 8 remain as real branches/conflicts; coverage_asymmetry is 0 (no silent extractor failures). Cost is ~84% below always-dual-builder and a fraction of a DeepSeek-extractor pipeline.
- Caveat: 'stable' here means structurally stable (coverage, folding, bounded DBA load, no extractor failures), NOT truthful. The remaining real branches are genuine cross-extractor divergences for a human/SPL to inspect, not resolved truths.

## Honesty / limits

- No truthfulness claim, no 'DESi solved hallucinations'. Metrics are epistemic structure, claim coverage, folding, DBA load, and compute efficiency only.
- Costs are list-price × token estimates (escalation Claude cost is actual tokens); real billing varies by provider routing. Full-100 token estimates use the hard-subset means and are an upper bound.
- DBA semantics depend on the cross-extractor region matcher (still phrasing-sensitive, per P30) — the next thing to harden, not a truth oracle.
- No new solver calls, no judge, no majority vote, no new intervention heuristics. Reused artifacts: P12 answers, P28 Granite graph, P30 Haiku cache. Ran offline; no key required; outputs secret-scanned.
