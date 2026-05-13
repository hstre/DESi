# Cycle 3 — Phase-III clip suppresses operational birth signal

## Hypothesis

Gen-cycle-2 of the generalization loop added `_clip_phase_overlaps`
to `detect_phases`: any earlier phase span that overlaps a later
phase is clipped to end at `later.start_loop - 1`. When
`terminal_failure_mode` is set, `detect_phase_v` extends its span
to end-of-trajectory regardless of post-trigger recovery.

If a trajectory has BOTH:
- a Phase V trigger (terminal_failure_mode set, or a single
  `dup > 0.50 AND novel <= 1` loop), AND
- a genuine_transformation_confirmed EN event AFTER the Phase V
  trigger,

then `detect_phase_iii` correctly identifies the birth span, but
`_clip_phase_overlaps` drops it entirely (because Phase V fully
covers it).

The composite classifier still produces `genuine_transformation_confirmed`
(so strict `birth(B) = 1` by the metrics-level definition), but the
Phase III span — the **operational** birth signal that downstream
LLM consumers see in the rendered report — is gone.

This is **birth(B) = 0 at the report / phase level** even though
the underlying metric says birth(B) = 1.

## Two-faced birth

The probe distinguishes:

- `confirmed_count` (composite-level birth): unchanged.
- `phase_iii_present` (operational-level birth): expected `False`.

Cycle 3 falsifies the *report-level* birth signal even when the
composite-level signal is preserved.

## Fixture

`fx3_terminal_failure_then_confirmed_birth.json`:
- 7 steps.
- Phase V hard trigger at loop 1 (dup=0.55, novel=1) AND
  `terminal_failure_mode = "NOVELTY_COLLAPSE"`.
- Recovery at loops 3-6: novel rebounds to 5, 5, 4, 3; dup falls
  to 0.20, 0.20, 0.22, 0.25.
- EN event at loop 3: `eni_novelty = 0.18`, `novel_claims_next = 5`,
  `dup_before = 0.55`, `dup_after = 0.22` → clean birth signature.

## Prediction

- composite label of EN: `genuine_transformation_confirmed`.
- `confirmed_count = 1`, so strict-metrics `birth(B) = 1`.
- `detect_phase_iii` finds the span at loops 4-6 (post-EN).
- `detect_phase_v` extends 1..6 (terminal failure → end).
- `_clip_phase_overlaps` drops Phase III (fully covered by Phase V).
- **`phase_iii_present = False`. Operational birth = 0.**

## Falsification criterion

The hypothesis is **falsified** iff the probe reports
`phase_iii_present = True`. Otherwise the report-level birth is
suppressed.
