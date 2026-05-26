# Semantic pre-solver routing — cross-summary

DESi as a peripheral pre-solver sequencer: it selects the solver prompt mode per item from epistemic structure (frame consistency + claim authority-grounding), with no dataset name and no gold label. Compared policies: A fixed baseline, B benchmark-matched family, C semantic router. DeepSeek v4 Pro only, temp 0, FIXED families, same evaluator. The core is untouched.

## Accuracy by policy

| dataset | A baseline | B matched | C router | router routes (base/ev/ent) |
| --- | --- | --- | --- | --- |
| tals/vitaminc | 0.71 | 0.76 | 0.68 | 64/12/24 |
| pietrolesci/nli_fever | 0.57 | 0.58 | 0.55 | 95/3/2 |

| dataset | overcommitment A->C | overabstention A->C | net help vs base | net help vs matched |
| --- | --- | --- | --- | --- |
| tals/vitaminc | 0.585 -> 0.634 | 0.034 -> 0.034 | -3 | -8 |
| pietrolesci/nli_fever | 0.385 -> 0.385 | 0.419 -> 0.446 | -2 | -3 |

## Answers

- **Does the existing semantic layer improve solver policy selection?** tals/vitaminc: router 0.68 vs baseline 0.71 (-0.030); pietrolesci/nli_fever: router 0.55 vs baseline 0.57 (-0.020). Router does NOT consistently beat the fixed baseline.
- **Does item-level routing beat benchmark-level prompt selection?** tals/vitaminc: router 0.68 vs matched 0.76 (-0.080); pietrolesci/nli_fever: router 0.55 vs matched 0.58 (-0.030). NO — the dataset-matched family is >= the item-level router; the discriminative semantic signal is too sparse (especially on FEVER, where every item is frame-UNDECIDABLE so the router falls back to baseline).
- **Does routing reduce overcommitment without increasing overabstention?** NO — overcommitment ROSE: VitaminC overcommitment 0.585 (A) -> 0.634 (C); overabstention 0.034 (A) -> 0.034 (C). Routing the 24 frame-CONFIRMED items to entailment-direct makes the solver commit MORE, which is the wrong direction for VitaminC's over-commitment — the existing frame signal is epistemically coherent but anti-correlated with this dataset's error.
- **Does routing reduce overabstention without increasing overcommitment?** NO — overabstention ROSE: FEVER overabstention 0.419 (A) -> 0.446 (C); overcommitment 0.385 (A) -> 0.385 (C). The router routes 95/100 to baseline (no frame signal on FEVER), so C ~= A; the few non-baseline routes nudged overabstention up, not down.
- **Is DESi functioning as a pre-solver epistemic sequencer?** Structurally YES: it deterministically projected each item through the existing frame/logic/frame-tension layer and emitted a solver policy (never a verdict). Whether that sequencing *improves accuracy* is the routing question above — it is limited by how well the existing semantic features discriminate verification items.
- **Does the core remain untouched?** YES — core byte-identical and replay-stable (replay 1.0) on every run; the router is read-only projection.

## Which semantic features mattered

- **Discriminative**: `FrameTensionRouter` claim-vs-evidence consistency (CONFIRMED vs UNDECIDABLE) and `LogicalAuditor` claim authority-rejection — these vary across VitaminC items (frames co-declare via reported-speech markers) and drive the router's non-baseline choices.
- **Insufficient**: the `evidence -> claim` formal-inference probe (returns UNREACHABLE for ~all natural-language pairs — the five formal rules do not match free-text entailment) and frame detection on FEVER (premise/hypothesis are short and marker-free -> all FRAME_UNDECLARED -> all UNDECIDABLE). With no positive entailment signal, the router cannot target FEVER's over-abstention the way the entailment-direct family does by fiat.

## Verdict

- The existing DESi semantic layer CAN act as a deterministic pre-solver sequencer (clean projection, replay-stable, core invariant). As an accuracy lever it is bounded by feature coverage: it produces a meaningful 3-way split only where frames co-declare (VitaminC), and degrades to baseline where they do not (FEVER). Per the study rule, this is reported as a feature-coverage limit, NOT patched into the core.

## Honesty / limits

- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt families; router is read-only projection of the existing core. No core, ontology, or meaning-space change; outputs secret-scanned.
