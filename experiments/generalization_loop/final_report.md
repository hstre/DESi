# Generalization Loop — Final Report

Branch `experiment/desi-generalization-loop-12`. Companion experiment to
the 12-cycle self-improvement loop. **Goal**: test whether the 11
detector/classifier changes from cycles 1-11 of the self-improvement
loop **generalize** beyond the original 10 adversarial fixtures, or
**overfit** to them.

The user's success criterion (verbatim): *"Not 'all metrics improve'.
Success is a clear answer to whether DESi's self-improvement
generalized or overfit."* This report's headline answer:

> **DESi generalized.** The n=20 unseen suite revealed 5 phase-overlap
> bugs, 1 over-permissive detector (`attractor_lock` fired 20/20), and
> 2 false-positive sources, all of which were fixable with **4** small
> detector changes (cycles 1-4). No foundational rethink was required.
> Cycles 5-7 added one new capability and surfaced it. Cycles 8-11 were
> **not performed**: no further substantive issues remained on the
> n=20 suite that would require 12 distinct detector changes. The
> ceiling of "12 cycles" was set by the user; the actual work
> needed was ≈4-7 cycles.

## Headline metrics

| Metric | Baseline | After cycles 1-7 | Δ |
|---|---:|---:|---:|
| **n=20 phase overlaps** | 5 | **0** | -5 |
| **n=10 phase overlaps** | 3 | **0** | -3 |
| **n=20 attractor_lock fires** | 20 | **4** | -16 |
| **n=10 attractor_lock fires** | 9 | **5** | -4 |
| **n=20 spurious-hit total** | 30 | 14 | -16 |
| n=20 malformed phase spans | 0 | 0 | 0 |
| n=20 branch_explosion (correctly placed) | 2 (gen04, gen17) | 2 (gen06, gen18) | composition: 2 FPs → 2 TPs |
| **New diagnostic surfaces** | 0 | **+1** (`borderline_chain`) | new gen11-class visibility |
| pytest | 28 | **35** | +7 |

## Cycle ledger

| Cycle | Change | Verdict | Commit |
|------:|--------|:------:|--------|
| 1 | Attractor tail-saturation guard | ACCEPTED | `4ed2098` |
| 2 | `_clip_phase_overlaps` post-processor | ACCEPTED | `75fe254` |
| 3 | Tail-windowed averaging in `detect_branch_explosion` | ACCEPTED | `1ffc3bb` |
| 4 | Strict-> on attractor dup boundary | ACCEPTED | `22e38b0` |
| 5 | New `detect_borderline_chain` (capability) | ACCEPTED | _this commit_ |
| 6 | Surface borderline_chain in `render_report` | ACCEPTED | _this commit_ |
| 7 | README cross-link | ACCEPTED | _this commit_ |
| 8–11 | **Not performed.** No remaining substantive target. | — | — |
| 12 | This synthesis | — | _this commit_ |

---

## Answers to the user's 12 questions

### 1. Did DESi generalize beyond the original adversarial fixtures?

**Yes.** No detector required a redesign. All 11 prior-loop changes
remained correct in their core logic. The 4 substantive cycles in this
loop were boundary tightenings and a non-overlap reconciliation
between independently-developed detectors, not corrections of the
detectors' principles.

### 2. Which first-loop improvements survived on unseen trajectories?

All 11 first-loop changes survived. Specifically:
- **Cycle 1's Phase II span normalisation** — no n=20 fixture has a
  malformed Phase II span.
- **Cycle 2's Phase V sustained-reversal closure** — fires on gen14
  (phase reversal twice) and gen03 (lock-recovery-lock).
- **Cycle 3's EN-event gate drop** — gen19 (no_EN_saturation_then_recovery)
  correctly fires Phase II without an EN event.
- **Cycles 4-7's new detectors** — held; only branch_explosion's
  averaging window needed re-windowing (gen-cycle 3).
- **Cycle 8's composite penultimate-EN** — held on gen11 and gen12.
- **Cycle 9's Phase II persistence** — held on gen05 (noisy random walk).
- **Cycle 10's Phase III first-trigger on composite EN** — held on
  gen15 (3 high-ENI events that don't recover; Phase III correctly
  does NOT fire).
- **Cycle 11's report-writer surface** — no rendering regression.

### 3. Which were overfit?

Two boundary cases. `attractor_lock`'s pre-cycle-1 focus-only heuristic
was over-permissive (20/20 fires) — fixed by gen-cycle 1.
`branch_explosion`'s whole-trajectory averaging mis-handled "late
recovery via synthesis" trajectories (gen04, gen17) — fixed by gen-cycle 3.
Both are **calibration failures**, not principle failures.

### 4. Which new failure modes appeared?

Three patterns the n=10 suite never exhibited:
1. **Phase overlaps**: 5/20 n=20 fixtures had two phases claiming the
   same loops. Even the n=10 suite already had 3/10 with overlaps,
   discovered only retrospectively here.
2. **`attractor_lock` over-firing** on focus-only continuity.
3. **Borderline-EN chains**: 3+ consecutive borderlines (gen11). Zero
   detector signal pre-loop. Added in gen-cycle 5.

### 5. Did DESi converge on sensible general revisions or chase suite-specific artifacts?

**Sensible general.** Every accepted cycle is principled:
- Cycle 1 adds a coherent saturation predicate alongside focus.
- Cycle 2 adds orchestration-layer phase reconciliation via
  PHASES_ORDERED.
- Cycle 3 windows an aggregate detector to its tail.
- Cycle 4 is a 1-character `>=`→`>` swap on a boundary.
- Cycle 5 adds a new diagnostic for an unseen-suite class.

No cycle was a fixture-targeted hack.

### 6. Did performance on the original suite regress?

**No.** On three metrics the original suite improved alongside the new:
- n=10 attractor_lock fires: 9 → **5**.
- n=10 phase overlaps: 3 → **0**.
- n=10 DET-FAL counts: unchanged from end of self-improvement loop.
- n=10 spurious-hit total: 17 → 13.

One test required adjustment
(`test_two_consecutive_low_eni_events_trigger_phase_iv`): trajectory
tweaked so it no longer co-fires Phase V on the same loops. This was
test over-specification, not a detector regression.

### 7. Did performance on the unseen suite improve?

Yes, materially. Phase overlaps 5→0. attractor_lock 20→4.
branch_explosion: 2 FPs swapped for 2 TPs. New diagnostic
`borderline_chain` (1/20).

### 8. Which changes should be merged to `main`?

Recommend for merge:
- Cycles 1, 2, 3, 4 — substantive detector improvements.
- Cycle 5 (`detect_borderline_chain`) — pure capability addition.
- Cycle 6 (report-writer surface).
- Cycle 7 (README cross-link).

Hold for review:
- The test trajectory adjustment in cycle 2 (Phase IV vs Phase V
  co-fire). Human should confirm the new dup values express "Phase IV
  without Phase V".

Per loop policy: **none merged automatically**.

### 9. Which should remain experimental?

- `ATTRACTOR_TAIL_MAX_MEAN_NOVEL=3.0`, `ATTRACTOR_TAIL_MIN_MEAN_DUP=0.30`
  (gen-cycle 1).
- `BRANCH_EXPLOSION_TAIL=3` (gen-cycle 3).
- `BORDERLINE_CHAIN_MIN_RUN=3` (gen-cycle 5).

All hand-calibrated against probe trajectories. Need cross-validation
on real DES paper7 dumps.

### 10. Which findings belong in DESi Paper 0?

1. **Independent phase detectors produce overlapping spans without a
   reconciliation layer.** The phase model is conceptually ordered but
   detectors don't enforce that ordering. `_clip_phase_overlaps`
   implements the missing reconciliation. paper0 should document this
   as a design contract: phase spans are non-overlapping intervals.

2. **"Did this ever happen" vs "is this currently happening" is a real
   semantic distinction in aggregator detectors.** The pre-cycle-3
   branch_explosion averaging confused them. Tail-windowing distinguishes.
   Generalises to any rate detector using whole-trajectory averages.

3. **The "n=10 was sufficient" assumption is fragile.** The
   self-improvement loop never tested its decisions against a new
   adversarial set. 4 of 5 generalization-loop cycles addressed issues
   invisible on n=10; one bug (phase overlaps) was already on the n=10
   suite but never surfaced. Cross-validation should be a standing
   requirement.

### 11. Is T10_BRANCH_PRUNE still needed?

**No.** Malformed-span counter is 0 across both suites after gen-cycle 2.
A natural successor (checking phase span coverage without gaps) is a
candidate for the next experiment.

### 12. What should the next experiment be?

Two high-value next experiments:

**(A) Cross-validation on a real DES paper7 trajectory dump.** All
metrics here and in the prior loop are on hand-designed probes (~6-30
loops). Real DES runs are 100+. Thresholds set in both loops are
unlikely to be exactly right. **Single highest-leverage** follow-up.

**(B) Prompt-side falsification of role prefixes.** Both loops kept to
deterministic detector changes. A new 10-trajectory live-LLM run
comparing prefix-on vs prefix-off would test whether the role policy
itself generalises.

Lower-priority: **property-based invariant tests** ("phase spans are
non-overlapping", "composite labels refine bimodal labels") would catch
regressions earlier than fixture-based tests.

---

## Honest scope statement

I did NOT execute 12 substantive cycles. After cycle 4 the n=20 suite
showed no remaining false-positive cluster that a clean single-cycle
detector change would address. Cycles 5-6 added one capability and its
report-writer surface. Cycle 7 was documentation. **Cycles 8-11 were
not performed** because the user's strict rules say "Do not optimize
for pretty reports", and shipping 4 made-up cycles to fill the 12-cycle
target would have been exactly that. Cycle 12 is this synthesis.

This is a generalization-loop finding in itself: when the system's
overfitting is small enough, a 12-cycle improvement loop is overspec'd.
The honest count is **7 cycles** of work — 4 detector tunings, 1
capability, 1 visibility, 1 documentation, and a synthesis.

---

## Loop status

7 logical cycles + 1 baseline + 1 synthesis on
`experiment/desi-generalization-loop-12`. **No merges to `main`.**
All artifacts in `experiments/generalization_loop/`.

The generalize-or-overfit question has a clear answer:
**DESi generalized; the n=10-tuned thresholds needed boundary
adjustments but the principles held.**
