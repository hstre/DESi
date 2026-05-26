# DeepSeek prompt-only calibration — summary

Only the evidence-style solver prompt changed (baseline vs calibrated). DeepSeek v4 Pro, direct, temp 0, one pass. No architecture/core/ontology change.

| dataset | variant | acc | overcommit | overabst | pred S/R/N |
| --- | --- | --- | --- | --- | --- |
| tals/vitaminc | baseline | 0.72 | 0.585 (24/41) | 0.017 (1/59) | 45/37/18 |
| tals/vitaminc | calibrated | 0.79 | 0.195 (8/41) | 0.186 (11/59) | 28/28/44 |
| pietrolesci/nli_fever | baseline | 0.55 | 0.385 (10/26) | 0.432 (32/74) | 13/39/48 |
| pietrolesci/nli_fever | calibrated | 0.53 | 0.269 (7/26) | 0.5 (37/74) | 7/37/56 |

## Answers

- **tals/vitaminc**: accuracy 0.72->0.79 (+0.070); overcommitment 0.585->0.195 (-0.390); overabstention 0.017->0.186 (+0.169).
- **pietrolesci/nli_fever**: accuracy 0.55->0.53 (-0.020); overcommitment 0.385->0.269 (-0.116); overabstention 0.432->0.5 (+0.068).

- **Did prompt-only calibration help?** see the deltas above (overcommitment on VitaminC, overabstention on FEVER) against the accuracy deltas.
- **Did overcommitment decrease?** VitaminC 0.585 -> 0.195.
- **Did overabstention decrease?** FEVER 0.432 -> 0.5.
- **Total accuracy improve or degrade?** tals/vitaminc 0.72->0.79; pietrolesci/nli_fever 0.55->0.53.
- **Is DeepSeek salvageable as semantic solver, or change model?** judged on whether NEI calibration improved WITHOUT collapsing SUPPORTS/REFUTES accuracy (per-class recall in the per-dataset reports); read from the numbers above, not asserted.

## DESi-core invariance

- recorded alongside every run: replay stable, core byte-identical, governance independent, mutation rejected -- unchanged by the prompt swap.

## Honesty / limits

- Prompt-only; N=100/dataset; one deterministic pass; DeepSeek mild non-determinism. No core change, no ontology drift; outputs secret-scanned.
