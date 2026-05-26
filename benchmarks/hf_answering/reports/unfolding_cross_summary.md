# Semantic-unfolding routing — cross-summary

Unfolding tests whether detecting *epistemically dangerous differences* under high surface similarity (directional / operator / relation / negation divergence) protects against false entailment folding. Policies: A baseline, B benchmark-matched, C DESi semantic-router, D micro-router, E unfolding-aware. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. Core untouched.

## Accuracy by policy

| dataset | A baseline | B matched | C DESi | D micro | E unfolding | fold candidates | unfold triggers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.73 | 0.77 | 0.7 | 0.71 | 0.72 | 85/100 | 78 |
| pietrolesci/nli_fever | 0.57 | 0.56 | 0.55 | 0.53 | 0.54 | 10/100 | 10 |

| dataset | overcommit A->E | overabst A->E | prevented false folds | over-protected | net vs micro |
| --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.585 -> 0.512 | 0.017 -> 0.102 | 10 | 10 | +1 |
| pietrolesci/nli_fever | 0.423 -> 0.269 | 0.392 -> 0.486 | 1 | 0 | +1 |

## Answers to the key questions

- **A) Does semantic unfolding outperform simple semantic routing?** tals/vitaminc: E 0.72 vs D(micro) 0.71 (+0.010), vs C(DESi) 0.7 (+0.020); pietrolesci/nli_fever: E 0.54 vs D(micro) 0.53 (+0.010), vs C(DESi) 0.55 (-0.010). E >= micro on both.
- **B) Can unfolding reduce false entailment routing?** prevented false folds tals/vitaminc: 10 prevented vs 10 over-protected; pietrolesci/nli_fever: 1 prevented vs 0 over-protected (net +1 across datasets). It DETECTS dangerous folds, but with low precision: prevention is largely offset by over-protection (catching a false fold costs a roughly equal number of correct folds), so it is not a net reducer of routing error here.
- **C) Can unfolding reduce overcommitment without collapsing into overabstention?** tals/vitaminc: overcommit 0.585->0.512, overabst 0.017->0.102; pietrolesci/nli_fever: overcommit 0.423->0.269, overabst 0.392->0.486.
- **D) Does this support 'semantic similarity alone is insufficient'?** The unfolding detector fires on high-similarity items (fold candidates) precisely where pure-similarity routing would fold; the directional/operator/relation/negation signals change the route on those items. Whether that *improves* accuracy is answered by (A)/(B) above -- the mechanism itself demonstrates that surface similarity and epistemic relation can diverge.
- **E) Does this validate semantic unfolding as a DESi-style concept?** Structurally YES: a clean, deterministic, replay-stable pre-solver layer that never touches the core. Empirically it is only MARGINALLY supported -- it edges the simpler routers by ~0.01 but its false-fold prevention is offset by equal over-protection (net ~0 on VitaminC) and it stays below baseline and the matched family; reported without overclaiming or any truthfulness claim.

- **vs benchmark-matched (B)**: matched still >= E (the dataset-level prompt remains the ceiling). **vs baseline (A)**: mixed.
- **Core untouched?** YES — byte-identical, replay 1.0 on every run.

## Which signals fired / were insufficient

- **tals/vitaminc**: {'fold_safe': 22, 'contradiction_masking': 38, 'directional_divergence': 2, 'semantic_near_epistemic_far': 3, 'partial_support_masking': 35}.
- **pietrolesci/nli_fever**: {'fold_safe': 90, 'semantic_near_epistemic_far': 8, 'partial_support_masking': 2}.
- Unfolding engages where surface similarity is high (VitaminC: evidence often restates the claim, so many fold candidates). On FEVER, hypotheses share little surface with short premises, so few fold candidates arise and unfolding mostly defers to the micro-router -- a coverage limit of lexical signals, not a core deficiency.

## Interpretation (per study rule)

- Mechanism validated, net benefit not. The directional / operator / relation / negation signals DO fire on high-similarity items and demonstrably re-route them, so 'semantic similarity alone is insufficient' holds at the MECHANISM level. But their PRECISION is too low for a net accuracy gain: each dangerous fold caught is roughly matched by a safe fold over-protected (net ~0 on VitaminC), and E stays below baseline and the matched family. Per the study rule this is reported as a signal-precision limit, NOT patched into the core. No truthfulness claim; DESi did not solve NLI.

## Honesty / limits

- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt families; detector deterministic and core-independent. No core, ontology, or meaning-space change; outputs secret-scanned.
