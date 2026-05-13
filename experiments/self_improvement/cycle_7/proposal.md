# Cycle 7 proposal — composite EN classification

Self-diagnosis (paper0/self_reflection.md §3): bimodal
`classify_en_event` thresholds at 0.10/0.12 are decoupled from
downstream effect. DET-FAL T1 (ENI=0.25, zero downstream) labelled
"genuine_transformation"; T2 (ENI=0.11, strong recovery) labelled
"borderline".

## Change

Add `classify_en_event_composite`. Six-cell label table over
`(eni_novelty bucket, recovered)`. Legacy `classify_en_event` is
**UNCHANGED**.

## Target failure

DET-FAL T1 + T2.

## Expected metric improvement

- New `en_classifications_composite` field on `DeterministicMetrics`.
- Tests 22 → 25.
- Counters don't move this cycle (legacy classifier unchanged);
  cycles 8–9 consume the new labels to actually resolve T1/T2/T6.

## Risk

Low. No prompt change. No semantics change in existing detectors.

## Not in this cycle

Penultimate-EN and Phase III still use legacy classifier (cycle 8).
