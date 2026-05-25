# P20 selective-DBA architecture benchmark (limit 100)

Architecture-behaviour measurement (NOT truthfulness). Offline reuse of P12/P14/P18/P19 artifacts; no model calls, no judge, no vote, no truth score. Measures branch inflation, false reconciliation, and escalation selectivity.

## Path distribution over the 100 items

- **folded / closed in single-builder path (no trigger): 75/100** — never reach DBA.
- triggered (ACTIVATE): 25/100.
  - of which **claim-less** (no atomic claims, nothing to reconstruct): 15 — logged, NOT escalated.
  - of which triggered-but-not-escalated (e.g. single trivial claim / matcher-level): 5.
- **escalated to DBA (claim-structural): 5/100** (tqa-0005, tqa-0007, tqa-0018, tqa-0027, tqa-0080).

## Escalated-set governed outcomes (P19)

| task | nα | nβ | P18 meaning class | typed divergences | P19 outcome | P18 would-reconcile? |
| --- | --- | --- | --- | --- | --- | --- |
| tqa-0005 | 3 | 3 | reconstruction_isomorph | - | **semantic_reconcilable** | yes |
| tqa-0007 | 4 | 4 | decomposition_variant | ['exclusivity_conflict', 'modality_flip', 'negation_flip'] | **logical_polarity_conflict** | yes |
| tqa-0018 | 2 | 2 | reconstruction_isomorph | - | **semantic_reconcilable** | yes |
| tqa-0027 | 4 | 2 | coarse_grain_equivalent | - | **semantic_reconcilable** | yes |
| tqa-0080 | 2 | 1 | coarse_grain_equivalent | - | **semantic_reconcilable** | yes |

- P19 governed outcomes: `{'semantic_reconcilable': 4, 'logical_polarity_conflict': 1}`
- P18 meaning classes (pre-governance): `{'reconstruction_isomorph': 2, 'decomposition_variant': 1, 'coarse_grain_equivalent': 2}`
- semantic reconciliations (closed by semantics): 4
- protected branches: 0
- logical polarity conflicts: 1
- guarded divergences: 0
- **cases P18 would have FALSELY reconciled, P20 protects: 1** (tqa-0007).

## Compute / folding

- second-builder (DBA) invocations: **5/100** vs always-dual-builder **100/100** -> **95% fewer** second-builder runs.
- the meaning-space + typed governance run only on the 5 escalated cases; of those, 4 are CLOSED by semantics and only 1 stay branched — so folding closes most of the little that escalates.

## Trigger usefulness (escalation precision)

How many of each trigger's firings actually reached DBA escalation (claim-structural). Low precision = too broad for DBA (still valid as a scorer-sensitivity log signal).

| trigger | fired | escalated | precision |
| --- | --- | --- | --- |
| judge_divergence | 23 | 4 | 4/23 |
| hallucination_judge_only | 5 | 1 | 1/5 |
| high_tie | 2 | 1 | 1/2 |

## Focus cases

- `tqa-0007`: escalated; meaning class decomposition_variant (region 0.871), divergences ['exclusivity_conflict', 'modality_flip', 'negation_flip'] -> **logical_polarity_conflict** (P18 false reconciliation PROTECTED)
- `tqa-0027`: escalated; meaning class coarse_grain_equivalent (region 0.786), divergences [] -> **semantic_reconcilable**
- `tqa-0080`: escalated; meaning class coarse_grain_equivalent (region 0.697), divergences [] -> **semantic_reconcilable**
- `tqa-0018`: escalated; meaning class reconstruction_isomorph (region 1.0), divergences [] -> **semantic_reconcilable**

## Reading (architecture behaviour, no truth claim)

- **Selective escalation works:** 5/100 reach the second builder; 75/100 fold/close on the single-builder path. DESi escalates rarely.
- **Less false branch inflation:** symbolic-only DBA branched 4/5 of the escalated set; the meaning-space closes most of those.
- **Less false reconciliation:** 1 case(s) the embedding would have merged are protected by typed governance (logical_polarity_conflict).
- **protected_branch_required / logical_polarity_conflict fire on a LOGICAL basis** (tqa-0007 negation flip), not on surface granularity — the intended behaviour.
- This is architecture behaviour only: it shows **less false branch inflation, less false reconciliation, more selective escalation** — NOT that DESi is 'more truthful'.

## Honesty / limits

- 5 escalated cases of one limit-100 run — indicative, not established at scale. Triggers/outcome mix will shift with data.
- Governance is precision-sound but recall-limited (negation_flip reliable; other typed checks barely exercised here). Folding closure is only as safe as that recall.
- No API calls, no new models, no truthfulness scores; persisted P18 Gβ and cached embeddings reused.
