# P21 trigger / folding optimization (limit 100, offline)

Operationalises DESi folding: a risk signal alone does not justify a second builder. Every triggered item is routed ESCALATE / LOG_ONLY / DISCARD by single-builder claim STRUCTURE. Reuses P12/P14/P18/P19/P20 artifacts; no API calls, no judge, no truthfulness score. This is architecture folding, NOT truthfulness tuning.

## Routing distribution

| class | count |
| --- | --- |
| folded | 75 |
| ESCALATE | 6 |
| LOG_ONLY | 3 |
| DISCARD | 16 |

## Second-builder call estimates

| policy | second-builder calls (of 100) | note |
| --- | --- | --- |
| always-dual-builder | 100 | run a 2nd builder on every item |
| P14 always-escalate-on-trigger | 25 | every ACTIVATE trigger -> DBA |
| P20 structural filter (select_cases) | 5 | implicit claim-structural filter |
| **P21 optimized ESCALATE** | **6** | explicit ESCALATE predicate + 3-class routing |

- unnecessary DBA cases removed vs P14: **19** (25 -> 6).
- compute saving vs always-dual-builder: **94% fewer** second-builder calls.
- P21 ESCALATE vs P20 structural set: P21 adds ['tqa-0000'], drops none. The additions come from the logical-risk-token rule (e.g. tqa-0000 'without harm' = a negation-class single claim): P21 is slightly MORE inclusive than the pure >=2-claims filter, a deliberate recall safeguard for logically-loaded single claims (+1 second-builder call here).

## Focus cases

- `tqa-0007`: **ESCALATE** (>=2 claims (4); >=2 types (3); causal); triggers ['judge_divergence'], nα=4.
- `tqa-0027`: **ESCALATE** (>=2 claims (4)); triggers ['high_tie'], nα=4.
- `tqa-0080`: **ESCALATE** (>=2 claims (2)); triggers ['hallucination_judge_only', 'judge_divergence'], nα=2.
- `tqa-0018`: **ESCALATE** (>=2 claims (2)); triggers ['judge_divergence'], nα=2.
- `tqa-0022`: **DISCARD** (already exact-resolved (accept_supported_exact)); triggers ['high_tie'], nα=1.

- tqa-0007 protection: PRESERVED — still ESCALATE (reaches DBA + typed governance).

## Which triggers leave DBA activation

| trigger | fired | -> ESCALATE | -> LOG_ONLY | -> DISCARD |
| --- | --- | --- | --- | --- |
| hallucination_judge_only | 5 | 1 | 2 | 2 |
| high_tie | 2 | 1 | 0 | 1 |
| judge_divergence | 23 | 5 | 3 | 15 |

- Triggers that retain real DBA activation: those with non-zero ESCALATE column (driven by claim structure, not answer-level uncertainty).
- Triggers that mostly drop to LOG_ONLY/DISCARD (too broad for DBA): judge_divergence / final_unknown_nonempty_raw / accept_uncertain on answers without claim-structural complexity — kept as LOG signals, not escalations.

## Honesty / limits

- **limit-100, tiny escalation base (6 cases).** The predicate is NOT overfit to those — it is a generic structural rule (claim count / types / compound / causal / logical-risk tokens), but its calibration is unproven beyond this run.
- **Recall risk:** by escalating on claim structure, a genuinely conflicting SINGLE-claim answer (no risk token) would be routed LOG_ONLY/DISCARD and NOT cross-checked. Single-claim matcher conflicts are handled by the P12 tie resolver, but a single-claim logical conflict outside that path could be missed. No guarantee all future conflicts are caught.
- This is **architecture folding, not truthfulness tuning**: it changes WHICH cases pay for a second builder, not any truth label. No new benchmark, intervention, model, or score.
- The escalation predicate is Alpha-only (single builder, pre-DBA): it cannot see the real typed divergence (that needs Beta); it approximates 'could diverge' from structure + logical-risk tokens.
