# Cycle 5 — Component ΔQ (Measurable Improvement)

## Paper 0 wording

> **ΔQ — Measurable Improvement**: At least some accepted revisions
> must improve measurable behavior — not merely style, agreement, or
> confidence.

Paper 0 §12.2 cites "FP: 4→0; FN: 5→2" as the ΔQ evidence.

## Strongest absence-hypothesis

The ΔQ figures are entirely **in-distribution**. The fixtures used to
measure FP and FN are the same fixtures DESi's rules were calibrated
against. There is **no held-out evaluation**. The improvement
demonstrates "the rules now correctly classify the test cases" — not
"the system has improved diagnostic competence".

Two cases:

1. **n=10 adversarial suite.** Authored by the same operator team
   that built DESi, with each fixture designed to exercise a specific
   DET-FAL ledger row. Tuning DESi to pass these tests is curve-fitting
   at the suite level.

2. **n=20 generalization suite.** Authored by me (Claude) WITH
   knowledge of post-cycle-11 DESi state. The `_meta` blocks of
   several fixtures (gen03, gen10, gen13) literally encode the
   *expected* DESi behaviour. The "Δ" of 0→20 phase overlaps to 0→0
   shows the suite passes the rules I introduced to pass it.

ΔQ as measured = "improvement on tests we wrote to expose then fix".
That is not the same as "measurable improvement of behaviour".

## Evidence in repo

- `data/adversarial/adv01..adv10.json` correspond 1:1 to DET-FAL T1..T10.
  Each fixture is a single-rule probe.
- `experiments/generalization_loop/generate_fixtures.py` `gen03_*`
  meta: *"Cycle 2 closed Phase V on reversal but doesn't re-open.
  Lock-recovery-lock pattern is new."* — fixture authored knowing
  what cycle 2 did and what it missed.
- `experiments/generalization_loop/generate_fixtures.py` `gen10_*`
  meta: *"adv09 had no terminal_failure_mode + recovered. This has
  both — tests the guard."* — fixture authored to test a specific
  gen-cycle-2 expectation.
- `paper0/run_role_policy_experiment.py` — the live-LLM experiments
  evaluated against a small fixed-trajectory set chosen by the operator.
- Zero references to a real DES paper7 trajectory dump being used for
  ΔQ measurement. (Paper 0 §11.10 acknowledges this.)

## Counter-evidence

- Paper 0's ΔQ wording does not require held-out evaluation. "At
  least some accepted revisions must improve measurable behavior."
  Measurable behavior = the counters DESi defines for itself.
  Those counters did move (FP 4→0, FN 5→2). ΔQ = 1 by Paper 0.
- Paper 0 §12.3 explicitly says "Birth does not prove generalization,
  domain transfer, long-horizon stability." So the in-distribution
  limit is acknowledged.
- Some improvements DO transfer in a weak sense: n=20 attractor_lock
  fires 20→4 ALSO showed n=10 attractor_lock fires 9→5. The cycle-1
  fix improved both suites. That's transfer evidence within the
  range of suites the operator built.

## Verdict

**ΔQ is SATISFIED under Paper 0's literal wording but is
in-distribution only.**

Three honest sub-claims:

- ΔQ > 0 on the n=10 suite (the suite DESi was designed against): YES.
- ΔQ > 0 on the n=20 suite (authored by me with knowledge of DESi state): YES.
- ΔQ > 0 on a distribution authored independent of DESi development: **UNKNOWN.**

Paper 0 cites the first as evidence and acknowledges the third is
open. So Paper 0's claim is internally consistent: ΔQ holds in the
sense Paper 0 commits to. To force ΔQ = 0 I would need to disprove
the in-distribution measurement, which I cannot — the metric counters
do move.

**Does not force birth(B) = 0.**

## Marginal epistemic gain

Non-zero. The honest reading: ΔQ is the weakest of the five
components in actual experimental support. It holds only because
Paper 0's wording is permissive about what "measurable behavior"
means. A stricter ΔQ definition (e.g., "measurable improvement on
trajectories generated independent of DESi development") would force
ΔQ = 0 today. Paper 0 §12.3 itself flags this.
