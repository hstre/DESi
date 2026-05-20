# Paper 10 — Go / No-Go Decision v2 (Adversarial Validation)

**Status:** decision artifact; not the paper itself.
This document supersedes `paper10_go_no_go.md` after the
v3.34..v3.36 adversarial validation sprint.

## Gate evaluation (directive § "Paper-10 Gate" v2)

| # | Gate | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | minimal_effective_hold (v3.34) | == 1   | **1**     | ✓ |
| 2 | specificity_score (v3.35)      | >= 0.80 | **0.588** | **✗** |
| 3 | noise_stability (v3.36)         | >= 0.80 | **1.000** | ✓ |
| 4 | timing_sensitivity (v3.36)      | > 0     | **20**    | ✓ |
| 5 | replay_stability (v3.36)        | == 1.0  | **1.000** | ✓ |

**4 of 5 pass. Gate #2 fails.**

## Decision

**Paper 10: NO-GO.**

The directive is explicit: *"Wenn eines scheitert: Kein
Paper. Weiterbauen."* Paper 10 must not be written until
the specificity gate is addressed.

## Why the specificity gate failed

v3.35 applied Strategy B (+1 confidence_hold + audit
withdraw) to every cliff-class universe member, not only
the 20 plateau trajectories. The action resolved all
20 plateaus AND also moved every CAUSAL_LEAP REJECTED
trajectory out of REJECTED.

| target_class | members | changed by Strategy B |
|---|---|---|
| `plateau`        | 20 | **20** (resolutions) |
| `causal_leap`    | 14 | **14** (false rescues) |
| `support_decay`  |  2 | 1 (depending on hash seed) |
| `frame_collision`|  0 | — |

The mechanism Strategy B uses — *withdraw the audit step*
— is generic. It works on plateau, on REJECTED CAUSAL_LEAP,
and (per v3.30 by design) on any trajectory the
cause-aware controller would otherwise have rolled back.

`specificity_score = plateau_resolutions
                   / (plateau_resolutions + false_rescues
                      + overcontrol)
                   = 20 / (20 + 14 + 0)
                   = 0.588`

Below the 0.80 threshold the directive sets.

## What v3.34 and v3.36 confirmed

The other four gates show that *the plateau itself* is
a real, stable structure:

* **v3.34**: minimal_effective_hold == 1. B0 (0 holds)
  resolves nothing; B1..B4 all resolve 20/20. Beyond
  k=1 there are diminishing returns
  (`diminishing_returns = True`) — the intervention is a
  delay/withdrawal effect, not a magnitude effect.
* **v3.36 noise**: scaling confidence by ±5 / ±10 / ±20%
  keeps every plateau trajectory at BRIDGE_REQUIRED
  under the simulated re-audit rule
  (`max(confidence) ≥ 0.5 → SUPPORTED`,
  `< 0.10 → REJECTED`, else plateau). All
  20 × 6 = 120 noise tests held the plateau;
  `plateau_breakpoints = 0`.
* **v3.36 timing**: pre-audit holds (t-1, t-2, t-3)
  each resolve all 20 plateaus; the after_audit holding
  point resolves zero. `timing_sensitivity = 20` — the
  *timing* matters but the magnitude does not.

So the plateau passes the hypothesis-shape tests
(stable, terminal, timing-sensitive, noise-robust).
It just isn't a class Strategy B treats specially.

## What this means for the paper

The paper would have claimed:
* the plateau is a distinct epistemic failure class,
* Strategy B is its specific intervention.

The v3.35 finding falsifies the second half. The paper
could instead claim:

* the plateau is a distinct *measurable* phenomenon
  (v3.31/32 census + cluster), and
* it shares its resolution mechanism with REJECTED
  trajectories (v3.35 cross-class) because the
  resolution mechanism is generic audit-withdrawal,
  not plateau-targeted.

Writing that paper requires re-framing the
contribution. The directive's gate is unforgiving: no
paper until specificity ≥ 0.80, or until the paper's
claim is rewritten to match the empirical specificity.

## Sources

* `artifacts/v3_34/report.json`            — hold-length sweep
* `artifacts/v3_34/hold_sweep.json`
* `artifacts/v3_35/report.json`            — cross-class transfer
* `artifacts/v3_35/cross_class_specificity.json`
* `artifacts/v3_36/report.json`            — noise + timing
* `artifacts/v3_36/plateau_noise_profile.json`
* `artifacts/v3_36/plateau_timing_profile.json`
* `artifacts/v3_36/plateau_validation_claims.json`

## What "weiterbauen" should look like

Two paths forward, neither in this sprint's scope:

1. **Build a plateau-specific intervention.** Find an
   action that resolves plateaus but does NOT resolve
   REJECTED trajectories of the same primary cause. The
   v3.35 measurement framework will report when such an
   action gets specificity ≥ 0.80.
2. **Re-frame the paper.** Drop the "Strategy B is
   plateau-specific" claim. Write a paper that
   characterises the plateau (real, stable, terminal,
   noise-robust, timing-sensitive) and explicitly
   notes that the only known resolution shares
   mechanism with REJECTED rescues.

Either path is a new sprint, not a free re-running of
v3.34..v3.36.

## Stop rules

* v3.34 documented `HOLD_SWEEP_DELAY_EFFECT` — sprint
  continued per the documented-not-aborted rule.
* v3.35 fired `HALT_LOW_SPECIFICITY` — sprint continued
  per the *weiterbauen* clause.
* v3.36 passed both `noise_stability` and
  `timing_sensitivity` thresholds.

Sprint complete. Paper 10: **NO-GO**.
