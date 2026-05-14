# Post-Phase-I/II-fix deltas

## What this cycle did

Patched `detect_phase_i` and `detect_phase_ii` in
`src/desi/phase_detector.py` to consult the `missing_metrics` signal
introduced by external-reality fix 1:

- **Phase I**: if step 0 has `novel_claims` or `dup_rate` in its
  `missing_metrics`, the detector returns **None** immediately. Pre-fix
  it would have emitted a medium-confidence Phase I because the
  defaulted-to-0 `dup_rate` accidentally satisfied the `<0.30`
  condition. The non-metric condition (no EN at loop 0) cannot carry
  Phase I alone.
- **Phase II**: the persistence-pair scan skips any adjacent pair
  where EITHER loop has `novel_claims` in its `missing_metrics`. Pre-fix
  all-zero defaulted `novel_claims` trivially satisfied `<=2` on every
  pair, producing low-confidence Phase II on null translator output.

Both detectors stay silent when essential metrics are missing.
The `schema_mismatch` detector (added by fix 1) is the canonical
place to surface "this trajectory has missing metric fields".

## Test suite

pytest: **45 → 49** (+4).

Four new tests:
1. Phase I silent when loop 0's metrics are missing.
2. Phase I still fires when metrics are explicit and conditions met
   (hand-authored regression).
3. Phase II silent when novel_claims is missing across the pair.
4. Phase II still fires on hand-authored collapse pattern.

## n=10 adversarial suite

| Metric | Pre-this-fix | Post-this-fix |
|---|---:|---:|
| Phase I fires (per-fixture count) | 10 / 10 | **10 / 10** |
| Phase II fires (per-fixture count) | 6 / 10 | **6 / 10** |
| attractor_lock fires | 5 | 5 |
| step_coherence_violation fires | 0 | 0 |
| spurious-hit total | 13 | 13 |
| phase overlaps | 0 | 0 |
| malformed phase spans | 0 | 0 |

**No regression.** All hand-authored adversarial fixtures provide
`novel_claims` and `dup_rate` explicitly; `missing_metrics` is empty
for every step; the new guards don't activate; Phase I and Phase II
fire exactly as before.

## n=20 generalization suite

| Metric | Pre-this-fix | Post-this-fix |
|---|---:|---:|
| Phase I fires (per-fixture count) | 18 / 20 | **18 / 20** |
| Phase II fires (per-fixture count) | 6 / 20 | **6 / 20** |
| attractor_lock fires | 4 | 4 |
| branch_explosion fires | 2 | 2 |
| step_coherence_violation fires | 2 | 2 |
| borderline_chain fires | 1 | 1 |
| spurious-hit total | 15 | 15 |
| phase overlaps | 0 | 0 |

**No regression.** Same reasoning as n=10: hand-authored fixtures
provide all metrics explicitly.

## External DES probe — conservative mode

This is the case the fix was designed for.

| Signal | Pre-fix | Post-fix |
|---|---|---|
| Phase I (0–0, medium, partial-match) | **fired** | **NOT fired** ✓ |
| Phase II (1–1, low) | **fired** | **NOT fired** ✓ |
| Any phase at all | I + II | **none** ✓ |
| `step_coherence` fires | 0 / 35 (already fixed in prior cycle) | 0 / 35 |
| `schema_mismatch` | True (35/35 missing both fields) | True (35/35 missing both fields) |
| `input_origin` disclaimer | fires | fires |

DESi now correctly emits **zero phases** on conservative-mode real DES
input, while the `schema_mismatch` detector explicitly says
"35/35 steps have missing metric fields; step-level metric diagnostics
are unreliable on this trajectory."

The report is now honest: no diagnostic is asserted on data that
cannot support it.

## External DES probe — heuristic mode

| Signal | Pre-fix | Post-fix |
|---|---|---|
| Phase I (0–0, medium) | fired | fired |
| Phase II (1–5, medium) | fired | fired |
| Phase V false-positive 10-11 | gone (fixed in prior cycle) | gone |
| `step_coherence` fires | 19 / 35 | 19 / 35 |
| `schema_mismatch` | False | False |

**Phase I and Phase II continue to fire in heuristic mode.** This is
correct: the heuristic explicitly provides `novel_claims` and
`dup_rate` (via H1 and H2), so `missing_metrics` is empty on every
step, and the guards correctly DO NOT activate. The diagnoses describe
H1/H2's output, which is what the `input_origin = translator_heuristic`
disclaimer warns the reader about.

## Summary

This is a one-shot extension of the prior `missing_metrics` plumbing
to two more detectors. No new diagnostic concepts were introduced.
The detectors that consult `missing_metrics` are now:

1. `validate_step_metric_coherence` (added in prior cycle).
2. `detect_phase_i` (this cycle).
3. `detect_phase_ii` (this cycle).

Three remaining downstream detectors (`detect_phase_iii`,
`detect_phase_iv`, `detect_phase_v`) consult only EN events and
not per-step novelty/duplication metrics directly, so they don't
need the guard. The aggregator detectors (`detect_branch_explosion`,
`detect_mild_stagnation`, `detect_terminal_attractor_subjects`,
`detect_borderline_chain`) do consume `novel_claims` and `dup_rate`,
but in averaging/aggregate form where missing fields default to 0.
On real DES data those defaults push the aggregates AWAY from the
thresholds (attractor needs mean_dup > 0.30; branch_explosion needs
avg_dup < 0.20 AND avg_novel >= 5; mild_stagnation needs
mean_novel ≤ 2.5 AND strictly increasing dup). All of them stay
silent on null inputs, which is the right behaviour. No further
patches needed.

## Verdict

Three external-reality fixes (prior cycle) + Phase I/II missing-metric
guards (this cycle) together resolve every interface-level failure
observed on the real DES upstream probe. DESi's diagnostic output on
real DES data is now:

- **`phases = []`** (no spurious assertions)
- **`schema_mismatch.detected = True`** (explicit "this is missing
  data, not contradictory data")
- **`input_origin = translated_DES_conservative`** with rendered
  disclaimer
- **all aggregate detectors silent** (correctly)
- **`step_coherence` silent** (correctly)

The underlying capability gap (real DES emits no ENI signal, so
`confirmed_genuine_en` cannot be derived) is unaddressed and not
addressable without DES-side changes — but DESi no longer lies about
this. It says "I cannot diagnose this trajectory at the per-loop
metric level" rather than mislabelling each step.

pytest: 49/49. n=10 adversarial: zero regression. n=20 generalization:
zero regression. External DES conservative: phases [] (was [Phase I,
Phase II]). External DES heuristic: unchanged (correctly).
