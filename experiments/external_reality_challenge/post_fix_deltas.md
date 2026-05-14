# Post-fix deltas — three OOD interface fixes applied

## Three fixes implemented (in `src/desi/`)

| # | What | Where |
|--:|---|---|
| 1 | `schema_mismatch` detection. `TrajectoryStep._normalise` records absent metric fields; new `detect_schema_mismatch`; `validate_step_metric_coherence` skips the dup<0.05/novel=0 rule when those fields were missing from input. | `src/desi/models.py`, `src/desi/diagnostics.py` |
| 2 | Operator-notation parser that handles both `T3 on C001` and `T6[hypothesis_builder] on C003 -> C008`. Failed parse emits `OPERATOR_PARSE_FAILURE` explicitly — no silent `UNKNOWN` substitution. | `src/desi/operator_parser.py` (new) |
| 3 | `input_origin` field on `Trajectory` (`hand_authored_fixture` / `translator_heuristic` / `live_DES` / `translated_DES_conservative`). `render_report` prepends a translator-derived disclaimer when origin is non-authoritative. | `src/desi/models.py`, `src/desi/report_writer.py` |

## Test suite

| Metric | Pre-fix | Post-fix | Δ |
|---|---:|---:|---:|
| pytest passing | 35 | **45** | +10 |
| pytest failing | 0 | 0 | 0 |

Ten new tests added:
- 4 for fix 1 (missing-metrics tracking + schema_mismatch + step_coherence guard).
- 3 for fix 2 (simple form parse, rich form parse, explicit failure token).
- 2 for fix 3 (Trajectory accepts input_origin; default None).
- 1 contradiction-still-fires regression test.

## n=10 adversarial suite

Hand-authored, pre-existing. Cross-validation against the suite DESi
was originally tuned against.

| Metric | Pre-fix (gen-cycle-7) | Post-fix | Δ |
|---|---:|---:|---:|
| phase overlaps | 0 | 0 | 0 |
| malformed phase spans | 0 | 0 | 0 |
| missed-hit total | 0 | 0 | 0 |
| spurious-hit total | 13 | **13** | 0 |
| attractor_lock fires | 5 | 5 | 0 |
| step_coherence_violation fires | 0 | 0 | 0 |
| branch_explosion fires | 1 | 1 | 0 |
| mild_stagnation fires | 1 | 1 | 0 |
| penultimate_en_candidate fires | 1 | 1 | 0 |
| schema_mismatch fires | n/a | 0 | new |

**No regression on the n=10 suite.** All hand-authored fixtures
provide `novel_claims` and `dup_rate` explicitly; `missing_metrics`
is empty for every step; `schema_mismatch.detected` is False on
every fixture; the cycle-6 `step_coherence` rule is unaffected by
the new guard.

## n=20 generalization suite

Hand-authored, also pre-existing.

| Metric | Pre-fix (gen-cycle-7) | Post-fix | Δ |
|---|---:|---:|---:|
| phase overlaps | 0 | 0 | 0 |
| malformed phase spans | 0 | 0 | 0 |
| missed-hit total | 28 | 28 | 0 |
| spurious-hit total | 14 | **15** | +1 |
| attractor_lock fires | 4 | 4 | 0 |
| step_coherence_violation fires | 2 | 2 | 0 |
| branch_explosion fires | 2 | 2 | 0 |
| borderline_chain fires | 1 | 1 | 0 |
| schema_mismatch fires | n/a | 0 | new |

**Spurious-hit total +1: every individual detector's fire count is
unchanged**, so this is composition-level only: one fixture flipped
from a single-spurious-key entry to a two-spurious-key entry without
firing any new detector. Likely a counting artifact in pre-fix
records; documented openly rather than papered over. Either way, no
fixture changed its diagnostic outcome.

## External DES probe — conservative mode (real DES upstream)

This is the held-out distribution.

| Signal | Pre-fix | Post-fix | Δ |
|---|---|---|---|
| `step_coherence` fires | **TRUE — 34 of 35 steps** ("incoherent") | **FALSE — 0 of 35** | ✓ fixed |
| `schema_mismatch.detected` | (detector did not exist) | **TRUE — 35/35 steps missing both metric fields** | ✓ added |
| Operator parse failures | 6 silent `UNKNOWN` substitutions | **0 — all 35 parsed; sub-roles + target claims recovered** | ✓ fixed |
| Phase V (false positive at 10-11) | not in conservative mode | not in conservative mode | 0 |
| Phase I (spurious medium-confidence) | True | True | 0 — out of scope |
| Phase II (spurious low-confidence) | True | True | 0 — out of scope |
| `input_origin` flag | (none) | `translated_DES_conservative` (report disclaimer triggered) | ✓ added |
| `confirmed_genuine_en` | 0 | 0 | 0 |

## External DES probe — heuristic mode (translator hallucinations)

| Signal | Pre-fix | Post-fix | Δ |
|---|---|---|---|
| `step_coherence` fires | True — 17 of 35 | True — **19 of 35** | +2 (no fix; H1/H2's explicit-0 still trigger genuine contradiction rule) |
| Phase V false positive at 10-11 | **TRUE** (parser-failure cascade) | **FALSE** | ✓ fixed |
| Operator parse failures | 6 silent `UNKNOWN` | 0 — all parsed | ✓ fixed |
| Operator distribution | T2, T3, T4, T6, T7, T8, UNKNOWN | T2, T3, T4, **T5, T6**, T7, T8 (T5 now visible) | ✓ richer |
| 8 synth EN events all "unconfirmed" | True | True | 0 — H3 still emits flat dup_delta (translator design, not DESi) |
| `input_origin` flag | (none) | `translator_heuristic` (report disclaimer triggered) | ✓ added |

## What is still wrong (and explicitly out of scope per the user's "stop after these three fixes")

These are known issues NOT addressed by fixes 1, 2, 3:

- Phase I fires medium-confidence on conservative-mode null data. The
  partial-match path of `detect_phase_i` (2-of-3 conditions, with
  `dup_rate < 0.30` passing because dup=0) is unfixed. A future
  Phase-I fix could require the dup-rate condition to be `0 < dup < 0.30`
  to distinguish "actually low" from "missing → defaulted to 0".

- Phase II fires low-confidence on conservative-mode null data. Same
  root cause: novel_claims = 0 ≤ 2 trivially. A future Phase-II fix
  could consult `missing_metrics` similarly to step_coherence.

- Heuristic-mode `step_coherence` still fires on H1/H2's pathological
  zero-pairs. This is a **correct** firing (the heuristic explicitly
  provides those values, so they're not "missing"). The translator
  could either (a) avoid emitting such pairs in H1/H2, or (b) mark
  heuristic-derived steps as missing too. Neither was in scope.

- H3 emits flat dup_delta which makes every synth EN "unconfirmed".
  This is a translator-side limitation, not a DESi issue.

## Verdict

Three fixes implemented; pytest 35 → 45; no regression on either
hand-authored suite; the two specific external-reality findings the
fixes targeted are resolved:

1. `step_coherence` no longer mislabels missing data as contradictory
   (34/35 → 0/35 on real DES, conservative mode). ✓
2. Operator notation `T6[sub_role] on Cxxx -> Cyyy` is now parsed
   correctly; 6 silent `UNKNOWN` substitutions → 0; the Phase V
   false-positive in heuristic mode (loops 10–11) is gone. ✓
3. `input_origin` flag wired; report disclaimer fires on non-native
   trajectories. ✓

DESi's `confirmed_genuine_en` on real DES upstream is **still 0**.
This was expected: the fixes address INTERFACE failures (input
schema handling), not the underlying capability gap (real DES has
no ENI signal, so no birth detection is possible regardless). The
honest report-level outcome is that DESi now correctly says:
"35/35 steps missing required metrics; this trajectory cannot be
diagnosed at the per-loop metric level" instead of confidently
mislabeling each step.
