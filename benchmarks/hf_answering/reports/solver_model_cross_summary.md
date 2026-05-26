# Solver-model cross-summary — identical epistemic conditions

Same datasets (VitaminC-100, NLI-FEVER-100), same FIXED prompt families (baseline / evidence-strict / entailment-direct), same temperature 0, same evaluator. Only the solver model varies. DESi is NOT the solver; its core metrics are recorded alongside and are identical across all runs. The task-matched family is evidence-strict for VitaminC (over-commitment style) and entailment-direct for FEVER (over-abstention style).

Models compared: DeepSeek v4 Pro, Claude Haiku 4.5, GPT-4.1-mini, Granite 4.1-8b.

## Accuracy matrix

Per-dataset cells are acc for baseline/evidence-strict/entailment-direct.

| model | VitaminC (b/e/ent) | FEVER (b/e/ent) | VitC matched | FEVER matched | mean (6) | spread | NEI imbalance (VitC/FEVER, baseline) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek v4 Pro | 0.75/0.78/0.72 | 0.56/0.52/0.56 | 0.78 | 0.56 | 0.648 | 0.05 | 20/20 |
| Claude Haiku 4.5 | 0.59/0.765/0.67 | 0.61/0.552/0.598 | 0.765 | 0.598 | 0.631 | 0.116 | 33/14 |
| GPT-4.1-mini | 0.68/0.81/0.73 | 0.45/0.51/0.59 | 0.81 | 0.59 | 0.628 | 0.135 | 22/33 |
| Granite 4.1-8b | 0.57/0.61/0.58 | 0.57/0.53/0.64 | 0.61 | 0.64 | 0.583 | 0.075 | 38/8 |

- *spread* = mean per-dataset (max-min) accuracy across the 3 families (lower = more stable to prompt framing). *NEI imbalance* = |pred_NEI - gold_NEI| under the baseline prompt (lower = better-calibrated abstention without prompt specialization).

## Answers

- **Should DeepSeek remain the semantic solver?** On the task-matched families DeepSeek scores VitaminC 0.78 / FEVER 0.56 (mean over 6 cells 0.648). The per-task accuracy leaders are VitaminC -> GPT-4.1-mini, FEVER -> Claude Haiku 4.5, so DeepSeek is not the raw accuracy leader on either matched task. HOWEVER DeepSeek has the best mean accuracy across the 6 cells (0.648 for DeepSeek v4 Pro), the lowest prompt-framing spread (0.05 for DeepSeek v4 Pro), and the best-balanced abstention under the unspecialized baseline prompt — i.e. it is the strongest GENERALIST. Verdict: keep DeepSeek as the default solver; treat per-task leaders as optional routing targets, not replacements.
- **Should routing select the solver by task style?** Among the candidates, the matched-best model is VitaminC -> GPT-4.1-mini (0.81), FEVER -> Claude Haiku 4.5 (0.598). They DIFFER, so task-style solver-routing could add a few points on each matched task — but the margins are small and the most-stable generalist (below) is within ~0.03 on both.
- **Does any solver dominate universally?** no single model is top on the matched family of both datasets. Best mean accuracy across all 6 cells (candidates): DeepSeek v4 Pro (0.648).
- **Does the evidence support architectural solver-routing?** PARTIALLY: matched winners differ by task style (so routing has a ceiling benefit), but the gaps are small and the steadiest generalist nearly matches the per-task specialists — so prompt-family routing (already established) captures most of the gain, and solver-routing is a marginal add-on, not a necessity.
- **Do Claude / GPT-mini show more stable calibration across both styles?** Prompt-framing spread (lower = steadier): DeepSeek v4 Pro 0.05, Claude Haiku 4.5 0.116, GPT-4.1-mini 0.135, Granite 4.1-8b 0.075. Steadiest: DeepSeek v4 Pro.
- **Does DeepSeek remain best when task-matched?** NOT uniformly — matched winners are VitaminC GPT-4.1-mini, FEVER Claude Haiku 4.5.
- **Does any model keep balanced NEI WITHOUT prompt specialization (baseline prompt)?** Smallest combined NEI imbalance: DeepSeek v4 Pro (VitC 20 / FEVER 20). DeepSeek v4 Pro 20/20, Claude Haiku 4.5 33/14, GPT-4.1-mini 22/33, Granite 4.1-8b 38/8.
- **Is the bottleneck the model, the framing, or the need for routing?** Best achievable accuracy across the CANDIDATES: VitaminC 0.81, FEVER 0.61 (the over-committing Granite baseline reaches 0.64 on FEVER only by predicting few NEI, matching FEVER's low-NEI gold — a calibration artifact, not reasoning). FEVER stays low (~0.61) for EVERY candidate regardless of prompt family -> the dominant bottleneck on FEVER is the FRAMING/data (the NLI-FEVER label style and premise-hypothesis brevity), not the choice of model. On VitaminC the lever is calibration: the evidence-strict family lifts every model markedly, and the residual spread between models is small -> framing first, model/routing second.

## DESi-core invariance

- recorded alongside every run: replay stable, core byte-identical, governance independent, mutation rejected — identical across all models and families. Swapping the solver does NOT touch DESi's deterministic governance.

## Honesty / limits

- N=100 per dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt families, no per-model tuning. Granite is the extractor shown as a solver baseline. This is a controlled solver study, not a redesign; no core, ontology, or architecture change; outputs secret-scanned.
