# Alexandria DBA prototype — first real dual-builder run (limit 100)

Selective dual-builder adjudication on the P14 ACTIVATE cases only. Builder Alpha = real DeepSeek/P3 claims; Builder Beta = a DELIBERATELY synthetic variant (documented perturbations). The diff engine and adjudication are real; the diff-type *distribution* reflects Beta's perturbations, not genuine model disagreement. No truth judged, no vote, no aggregation — only typed, explained differences.

## Activation

- cases processed (ACTIVATE only): **25/100** (always-on would be 100/100).
- of these, **15** had zero Alpha claims (claim-less answers — nothing to reconstruct).

## Diff types observed (total across cases)

| diff_type | count |
| --- | --- |
| missing_claim | 6 |
| uncertainty_divergence | 6 |
| assumption_mismatch | 3 |
| relation_mismatch | 2 |

## Adjudication outcomes

| outcome | cases |
| --- | --- |
| convergence | 20 |
| refinement | 0 |
| stable_ambiguity | 2 |
| formal_error | 0 |
| branch_required | 3 |
| undecidable | 0 |

## Per-case (ACTIVATE)

| task | n_alpha | n_beta | outcome | top diffs | activating triggers |
| --- | --- | --- | --- | --- | --- |
| tqa-0000 | 1 | 1 | convergence | - | ['judge_divergence'] |
| tqa-0005 | 3 | 3 | branch_required | assumption_mismatch:1, missing_claim:1, relation_mismatch:1, uncertainty_divergence:2 | ['judge_divergence'] |
| tqa-0007 | 4 | 5 | branch_required | assumption_mismatch:2, missing_claim:1, relation_mismatch:1, uncertainty_divergence:2 | ['judge_divergence'] |
| tqa-0015 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0017 | 0 | 0 | convergence | - | ['hallucination_judge_only', 'judge_divergence'] |
| tqa-0018 | 2 | 2 | stable_ambiguity | uncertainty_divergence:1 | ['judge_divergence'] |
| tqa-0022 | 1 | 1 | convergence | - | ['high_tie'] |
| tqa-0027 | 4 | 0 | branch_required | missing_claim:4 | ['high_tie'] |
| tqa-0031 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0032 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0035 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0037 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0045 | 0 | 0 | convergence | - | ['hallucination_judge_only', 'judge_divergence'] |
| tqa-0050 | 1 | 1 | convergence | - | ['hallucination_judge_only', 'judge_divergence'] |
| tqa-0054 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0066 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0068 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0072 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0076 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0080 | 2 | 2 | stable_ambiguity | uncertainty_divergence:1 | ['hallucination_judge_only', 'judge_divergence'] |
| tqa-0081 | 1 | 1 | convergence | - | ['judge_divergence'] |
| tqa-0085 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0089 | 0 | 0 | convergence | - | ['judge_divergence'] |
| tqa-0091 | 1 | 1 | convergence | - | ['hallucination_judge_only', 'judge_divergence'] |
| tqa-0098 | 0 | 0 | convergence | - | ['judge_divergence'] |

## Known forensic cases

- `tqa-0022`: outcome **convergence** (n_alpha 1, diffs {}, activated by ['high_tie']).
- `tqa-0027`: outcome **branch_required** (n_alpha 4, diffs {'missing_claim': 4}, activated by ['high_tie']).

## Reading (honest)

- **Does DBA work end-to-end?** Yes mechanically: trigger -> Alpha -> Beta -> canonical graphs -> diff engine -> adjudication runs over all 25 ACTIVATE cases and emits typed diffs + a non-truth outcome.
- **Where the 20 convergences come from.** Of 25 ACTIVATE cases, **15 have NO atomic claims** (abstained/short answers) — DBA has nothing to reconstruct, so they converge trivially. Only **10** carry claims; of those **5** produced a real typed divergence (branch_required/stable_ambiguity) and the rest were single/simple claims.
- **Which diff types really occurred?** missing_claim, uncertainty_divergence, assumption_mismatch, relation_mismatch (see table). With the synthetic Beta these reflect its perturbations, not real model disagreement — a REAL Builder Beta is needed before the distribution is meaningful.
- **KEY INSIGHT — high_tie is an ANSWER-level signal, DBA is CLAIM-level.** The canonical cases split: `tqa-0027` (4 claims) -> **branch_required** (visible typed difference), but `tqa-0022` (1 trivial claim) -> **convergence**. The tqa-0022 ambiguity lives in answer-vs-gold *matching* (the matcher tie), not in claim *reconstruction* — so a matcher trigger does not reliably yield a claim-level diff. DBA and the matcher-tie are orthogonal layers; this is the main architectural finding.
- **Stronger than a judge?** For the cases with real structure, yes architecturally: instead of one authority labelling truth, DBA names *what* differs and routes (keep both / refine / branch) without saying who is right. But it is NOT a drop-in for the matcher-tie problem — it is complementary, operating on reconstruction structure, not answer scoring.
- **Unnecessary triggers (for DBA).** The 15 claim-less activations (mostly judge_divergence / final_unknown_nonempty_raw on short/abstained answers) gave DBA nothing — these are weak DBA triggers and should be LOG-only for the cross-assessment path (they remain valid scorer-sensitivity signals). high_tie alone is also weak for DBA unless the answer has multi-claim structure.
- **New triggers worth considering (claim-structure, scorer-independent):** compound/causal objects (granularity + assumption risk), >=2 atomic claims or >=2 claim types (relation grouping), and per-claim modality/uncertainty spread — these predicted the actual divergences here and need no truth scorer.

## Honesty / limits

- **Builder Beta is synthetic** (deterministic perturbations of Alpha), NOT an independent model. This validates the architecture and diff taxonomy, not builder quality or real disagreement rates.
- No API calls, no new truthfulness scores, no intervention/SPL changes, no judge, no majority vote, no aggregation.
- The next real stage requires a genuinely independent Builder Beta (e.g. Granite) so the diff/outcome distribution reflects real model divergence rather than scripted perturbations.
