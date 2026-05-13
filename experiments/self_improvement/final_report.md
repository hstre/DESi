# Self-Improvement Loop — Final Report

12 cycles on branch `experiment/desi-self-improvement-loop-12`.
DESi-self-diagnosed candidates from `paper0/self_reflection.md` and
the cycle-to-cycle "next hint" chain. No prompt and no detector
changes in the same cycle. Failed attempts preserved.

## Headline metric delta (n=10 adversarial set)

| Metric                           | Start (paper0 head `f89417a`) | End (cycle 11 `2cf9264`) |
|----------------------------------|------------------------------:|-------------------------:|
| `false_positive_count` (DET-FAL) | **4** | **0** |
| `false_negative_count` (DET-FAL) | **5** | **2** |
| `malformed_phase_span_count`     | **1** | **0** |
| pytest cases                     | 13    | **28** |
| New deterministic detectors      | 0     | **+3** (branch_explosion, mild_stagnation, step_coherence) |
| New classifiers                  | 0     | **+1** (composite EN, 6 labels) |
| LLM-side runs in the loop        | 0     | 0 (per "measure first") |

Remaining FNs are T1 (high-ENI no-recovery) and T2 (low-ENI with
recovery) — they are addressed at the *classification layer* via
cycle 7's composite labels, but the legacy bimodal classifier (which
the DET-FAL ledger counts) is intentionally untouched so downstream
phase-III/phase-II logic keeps stable. Cycles 8 and 10 switched
consumers (penultimate-EN, Phase III first-trigger) to composite.

## Cycle ledger

| Cycle | Change                                                          | Verdict             | Commit       |
|------:|-----------------------------------------------------------------|:-------------------:|--------------|
| 1     | Normalise Phase II span bounds                                  | ACCEPTED            | `378909c`    |
| 2     | Close Phase V on sustained reversal                             | ACCEPTED            | `5f04fe2`    |
| 3     | Drop EN-event gate from Phase II                                | ACCEPTED            | `1953bc8`    |
| 4     | New `detect_branch_explosion`                                   | ACCEPTED            | `1f642e2`    |
| 5     | New `detect_mild_stagnation`                                    | ACCEPTED            | `5a854d3`    |
| 6     | New `validate_step_metric_coherence` (defensive)                | ACCEPTED (defensive)| `4c6c571`    |
| 7     | New composite EN classification (capability)                    | ACCEPTED (capability) | `217a457`  |
| 8     | Switch penultimate-EN to composite classifier                   | ACCEPTED            | `b28755d`    |
| 9     | Phase II persistence requirement                                | ACCEPTED            | `f05c08a`    |
| 10    | Phase III first-trigger on composite EN                         | ACCEPTED (defensive)| `cec32a6`    |
| 11    | report_writer surfaces cycle 4-7 detectors + cycle-10 test repair | ACCEPTED          | `2cf9264`    |
| 12    | this synthesis                                                   | —                   | _this commit_ |

---

## §1 — Which changes improved DESi?

**Measured improvements** (count moved a primary metric):

- Cycle 1 (`378909c`): malformed_phase_span_count 1 → 0.
- Cycle 2 (`5f04fe2`): DET-FAL false_positive_count 4 → 2 (T9, T10).
- Cycle 3 (`1953bc8`): false_negative_count 5 → 4 (T8 saturation
  without EN).
- Cycle 4 (`1f642e2`): false_negative_count 4 → 3 (T7 branch
  explosion).
- Cycle 5 (`5a854d3`): false_negative_count 3 → 2 (T4 mild
  stagnation).
- Cycle 8 (`b28755d`): false_positive_count 2 → 1 (T6 penultimate
  unconfirmed).
- Cycle 9 (`f05c08a`): false_positive_count 1 → 0 (T5 Phase II
  oscillation).

**Capability adds without immediate counter movement** but useful
for downstream cycles:

- Cycle 6 (`4c6c571`): metric coherence guard (defensive; 0/10
  trajectories incoherent in the adversarial set).
- Cycle 7 (`217a457`): composite EN classifier (consumed by cycles
  8 and 10).
- Cycle 10 (`cec32a6`): Phase III first-trigger on composite EN
  (defensive; no current adversarial trajectory exercises the
  guard).
- Cycle 11 (`2cf9264`): report-writer surface + cycle-10 test
  repair.

## §2 — Which worsened DESi?

No cycle worsened a primary metric. **Two cycles documented failed
attempts** that were caught pre-commit and reverted:

- Cycle 2 first impl closed Phase V on reversal regardless of
  `terminal_failure_mode`. adv03 regressed (V 2..5 → 2..2 across an
  EN-driven dip). Reverted by adding the `has_terminal_failure`
  guard; preserved in `cycle_2/evaluation.md`.
- Cycle 10 first impl switched **both** the first-trigger and the
  next-genuine boundary in `detect_phase_iii` to composite. adv06
  Phase III extended to 2..6, overlapping Phase V (4..6) — exactly
  the T9-shape FP that cycle 2 resolved. Reverted by keeping the
  boundary on the legacy classifier; preserved in
  `cycle_10/evaluation.md`.

One **defect** record:

- Cycle 10's MCP push omitted `tests/test_phase_detector.py` from
  its `files` list. The new regression test
  `test_phase_iii_requires_confirmed_genuine_en_after_cycle_10`
  passed in pre-push smoke but never reached the remote commit.
  Cycle 11 restored it.

## §3 — Which metrics were gamed or misleading?

- **DET-FAL `false_negative_count` for T1/T2** is sensitive to *which
  classifier* you count. The legacy bimodal classifier remains
  decoupled from recovery (T1: high ENI, no recovery → still
  "genuine_transformation"; T2: low ENI, real recovery → still
  "borderline"). Cycle 7 added a composite classifier that gets the
  labels right, and cycles 8 and 10 made the principle / Phase III
  consume it. But if you read the *legacy labels* you see no change.
  This is the kind of metric drift the user's strict rules warned
  about; documented above.
- **"Defensive cycles" don't move counters.** Cycles 6, 10, 11 are
  defensive: they add capability or visibility without changing the
  10 adversarial trajectories' phase output. By the user's primary-
  metric measure, they look like no-ops. They are not — they protect
  against future shapes — but a naive read of the DET-FAL counters
  underestimates them.
- **The cycle-10 internal-inconsistency** (commit message claimed
  "27 → 28" tests but pushed only 27) is the loop's most candid
  failure: the *evaluation report* was correct in describing what
  the cycle *should* have shipped, and wrong about what actually
  shipped. Cycle 11 documented and fixed this.

## §4 — Did DESi converge on sensible revisions?

**Yes**, on the deterministic side. The "next-cycle hint" chain
(generated by each cycle's evaluation pointing to a specific item
in `paper0/self_reflection.md`) advanced cleanly through §6.1
(branch_explosion), §6.2 (mild_stagnation), §6.3
(saturation-without-EN), §6.4 (phase reversal), §6.5 (metric
coherence), §3 (composite EN), and §4.4 mutex (deferred — no
overlap on current set).

Two cycles required a **failed-attempt revision**: cycle 2's
terminal-failure guard and cycle 10's boundary-stays-legacy.
Both were caught by direct measurement on the n=10 set before
commit. This is "convergence with one correction step" — not silent
convergence.

DESi did **not** address the prompt-side hint (§6.6 synthesizer
evidence-link guard / P13 echo-chamber bypass). That would require
a prompt change and an LLM re-run; this loop kept to detector-only
changes for budget and reproducibility.

## §5 — Did the loop collapse into self-confirmation?

Two evidence pieces against collapse:

- **Failed attempts were preserved**, not deleted, per strict
  rule 4. Cycles 2 and 10 each carry a "Failed-attempt record"
  section. The cycle-10 push defect (test omitted) was caught and
  documented in cycle 11.
- **Defensive cycles were marked as such**. Cycles 6 / 10 / 11 are
  ACCEPTED (defensive) — i.e., they don't move the DET-FAL counter.
  Marking them differently from the substantively-moving cycles
  resists the temptation to claim every cycle as a win.

Two evidence pieces for partial collapse:

- The loop **never tested its own decisions against a *new*
  adversarial set**. Every metric in this report is on the same
  10 trajectories DESi was tuned against. A trajectory shape the
  loop didn't design for (e.g., DES paper7 real run) will reveal
  threshold drift the n=10 set can't.
- The "ACCEPTED (capability)" verdict on cycles 6, 7, 10, 11 is
  a soft category that masks "didn't move the metric this cycle".
  Honest, but it accumulates.

Net: the loop did not collapse. It did, however, run out of
DET-FAL-counter-moving work after cycle 9; cycles 10-11 are
honestly described as defensive / housekeeping.

## §6 — What should be merged to `main`?

Recommend for merge (zero or positive impact, well-tested):

- Cycles 1, 2, 3, 4, 5, 7, 8, 9 — the core moving-counter cycles.
- Cycle 6 (defensive metric-coherence guard) — pure addition, no
  risk.
- Cycle 11 (report-writer surface + cycle-10 test repair).

Hold-back for further review before merge:

- Cycle 10 (Phase III first-trigger on composite). It is defensive
  on n=10; the calibration of `confidence="medium"` when in_band
  drops below half the window length should be re-examined against
  a real DES paper7 trajectory before merging — the cycle-10 failed
  attempt showed it is easy to extend Phase III into Phase V
  territory when the EN composite distinguishes confirmed from
  unconfirmed but the boundary classifier doesn't.

Per the loop's branch policy: **none merged automatically**. Human
review final.

## §7 — What should remain experimental?

- The DETECTOR thresholds calibrated to n=10:
  `BRANCH_EXPLOSION_MIN_BRANCHES=5`, `MILD_STAGNATION_TAIL=5`,
  `MILD_STAGNATION_MAX_AVG_NOVEL=2.5`, the metric-coherence
  impossibility rules. All hand-set against probe-length
  trajectories (~8 loops). Real DES paper7 runs go 30+. Treat as
  experimental until cross-validated.
- The composite EN classifier's 6-cell label table is calibrated to
  the same n=10 plus the cycle-7 bench tests. Should be exercised
  on a live DES dump before being treated as authoritative.
- The Phase II persistence rule (≥2 consecutive novel≤2) — works
  on n=10 but is the kind of rule that brittle thresholds break.

## §8 — What should become paper0 material?

Three findings that belong in paper0 / the next falsification pass:

1. **The composite EN classifier resolves the bimodal-threshold
   pathology, but only when consumers actually adopt it.** Cycles
   7-8-10 together demonstrate that "add capability" → "switch
   consumer" → "verify no regression" is the correct three-step
   shape for fixing a label that's used in multiple places. Cycle
   10's failed attempt is the cautionary tale: switching the
   classifier in *some* lookups but not *all* lookups in the same
   function can re-introduce a different bug.
2. **DESi's phase model is sensitive to which "genuine_transformation"
   means.** The cycle-10 regression on adv06 shows that Phase III's
   window boundary is materially affected by whether
   `genuine_transformation_unconfirmed` is treated as "still high
   ENI" or "not genuine". paper0 should document this clearly:
   the window-boundary semantic is *not* the same as the
   first-trigger semantic, and conflating them re-creates
   Phase III ∩ Phase V overlap.
3. **Defensive-only cycles look like no-ops to a counter-only
   reading, but they make the system smaller in failure surface.**
   The loop's mid-cycles (6, 10, 11) added forward-looking
   protection without moving the DET-FAL counter. They are real
   work; the user's "Optimize for measured improvement" instruction
   correctly didn't elevate them but should not be read as their
   being wasted.

Things that did **not** make it into this loop and should be future
paper0 cycles:

- **Prompt-side synthesizer evidence-link guard** (RPP-STR P13
  echo-chamber bypass). Requires a prompt change and an LLM
  re-evaluation. Skipped here to stay deterministic; should be the
  first prompt-side cycle of a follow-up loop.
- **Cross-validation on a real DES paper7 trajectory dump**. All
  metrics here are on the n=10 hand-designed adversarial set.
  Replication on a real dump is the single highest-leverage next
  step.
- **Phase III ∩ Phase V mutex as a defensive aggregator pass.** No
  current overlap exists, but the cycle-10 failed-attempt shows
  one can be reintroduced by a "natural" change.

---

**Loop status**: complete. 12 commits on
`experiment/desi-self-improvement-loop-12`. No merges to `main`.
All cycles documented in `experiments/self_improvement/cycle_N/`.
The headline shift on the n=10 adversarial set:

- **false_positive_count 4 → 0**
- **false_negative_count 5 → 2**
- **malformed_phase_span_count 1 → 0**
- **pytest 13 → 28**.
