# Residual semantic escalation — cross-summary

Algorithm-first + semantic-residual escalation: deterministic layers resolve clear cases; only the ambiguous residue escalates to a lightweight deterministic semantic scorer (synonym-group + char-trigram vectors, directional containment / asymmetry; no learned embeddings available offline). Policies A baseline / B matched / C DESi router / D micro / E unfolding / F residual. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. Core untouched.

## Accuracy by policy

| dataset | A base | B matched | C DESi | D micro | E unfold | F residual | escalated | esc. acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.72 | 0.768 | 0.72 | 0.72 | 0.73 | 0.72 | 45/100 | 0.689 |
| pietrolesci/nli_fever | 0.54 | 0.58 | 0.53 | 0.53 | 0.54 | 0.54 | 10/100 | 0.5 |

| dataset | overcommit A->F | overabst A->F | false folds prevented | over-protected | net F vs E | esc net vs E |
| --- | --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.561 -> 0.488 | 0.034 -> 0.119 | 8 | 10 | -1 | -1 |
| pietrolesci/nli_fever | 0.462 -> 0.269 | 0.432 -> 0.486 | 4 | 8 | +0 | +0 |

## Answers to the key questions

- **A) Does residual semantic escalation improve unfolding precision?** tals/vitaminc: F 0.72 vs E 0.73 (-0.010); on the escalated subset F net vs E = -1 (esc. acc 0.689); pietrolesci/nli_fever: F 0.54 vs E 0.54 (+0.000); on the escalated subset F net vs E = +0 (esc. acc 0.5). F does NOT consistently beat E.
- **B) Can residual-only semantics outperform pure lexical unfolding?** see (A): not clearly -- escalation net vs E across datasets = -1.
- **C) Reduce false entailment folds without massive overabstention?** tals/vitaminc: prevented 8 / over-protected 10; overabst 0.034->0.119; pietrolesci/nli_fever: prevented 4 / over-protected 8; overabst 0.432->0.486.
- **D) Does this validate 'semantic vectors are useful for unfolding, not just folding'?** The residual vectors are applied ONLY to detect dangerous/ambiguous folds (directional containment + asymmetry + same-topic checks), never to merge items; whether that yields a net accuracy gain is answered by (A)/(B) -- mechanism demonstrated, net gain marginal/absent. The vectors here are deterministic local lexical-semantic vectors, not learned embeddings (none available offline); a stronger test would need real embeddings.
- **E) Does this support progressive epistemic escalation?** Structurally YES: most items are resolved by the deterministic layers and only 45/10 items per dataset escalate; the escalation is cheap, deterministic, replay-stable, and never touches the core. Empirically the accuracy gain is marginal -- the residual signal is not precise enough to beat the matched family.

- **vs benchmark-matched (B)**: matched still >= F (dataset-level prompt remains the ceiling). **vs baseline (A)**: F >= baseline on both. **vs micro (D)**: F >= D on both.
- **Core untouched?** YES -- byte-identical, replay 1.0 on every run.

## Interpretation (per study rule)

- F does not clearly improve. The residual signals that remain INSUFFICIENT: directional containment built from synonym-group + char-trigram vectors catches morphological/subset overlap but still cannot recognise paraphrastic entailment (different surface forms, same meaning) -- which needs learned embeddings, unavailable offline here. The escalation mechanism (algorithm-first, residue-only) is validated structurally; the residual SIGNAL is the limiting factor. Reported as a signal limit, NOT patched into the core. No truthfulness claim; DESi did not solve NLI.

## Honesty / limits

- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt families; residual vectors are deterministic local lexical-semantic vectors (no learned embeddings offline); core-independent. No core/ontology/meaning-space change; outputs secret-scanned.
