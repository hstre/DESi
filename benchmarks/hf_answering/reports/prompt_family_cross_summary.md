# Prompt-family cross-summary — DeepSeek task-matched calibration

Prompt-only (model/temp/evaluator/core all identical). evidence-strict targets over-commitment; entailment-direct targets over-abstention. The 'universal' prompt = evidence-strict applied to both.

| dataset | metric | baseline | evidence-strict | entailment-direct |
| --- | --- | --- | --- | --- |
| tals/vitaminc | accuracy | 0.73 | 0.78 | 0.73 |
| tals/vitaminc | overcommit | 0.537 | 0.22 | 0.488 |
| tals/vitaminc | overabst | 0.034 | 0.203 | 0.017 |
| pietrolesci/nli_fever | accuracy | 0.57 | 0.54 | 0.58 |
| pietrolesci/nli_fever | overcommit | 0.346 | 0.269 | 0.385 |
| pietrolesci/nli_fever | overabst | 0.419 | 0.486 | 0.405 |

## Answers

- **tals/vitaminc**: baseline 0.73, evidence-strict 0.78, entailment-direct 0.73 -> best accuracy: **evidence_strict**; task-matched family (evidence_strict) == best.
- **pietrolesci/nli_fever**: baseline 0.57, evidence-strict 0.54, entailment-direct 0.58 -> best accuracy: **entailment_direct**; task-matched family (entailment_direct) == best.

- **Can DeepSeek be stabilized by task-specific calibration?** Compare each dataset's task-matched family to its baseline (accuracy + the targeted error rate) above.
- **Which prompt family fits which benchmark style?** evidence-strict for over-commitment (VitaminC-style); entailment-direct for over-abstention (FEVER/NLI-style) -- judged by which family minimizes the dataset's characteristic error above.
- **Does one universal epistemic prompt fail systematically?** The universal (evidence-strict) row vs the entailment-direct row on FEVER shows whether a single prompt mis-serves the opposite failure mode.
- **Does prompt-family specialization outperform model replacement?** If the matched family recovers accuracy on both styles without collapse, specialization is sufficient and no model swap is indicated; otherwise it is.
- **Should Granite->DeepSeek continue?** This study is solver-only (DeepSeek direct, no Granite in the loop); it speaks to the SOLVER's calibratability, not the extractor pairing -- reported as such.

## DESi-core invariance

- recorded alongside every run: replay stable, core byte-identical, governance independent, mutation rejected -- unchanged by any prompt family.

## Honesty / limits

- Prompt-only; N=100/dataset; one deterministic pass; mild non-determinism; no core/architecture/ontology change; outputs secret-scanned.
